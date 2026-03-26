from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import logging
from threading import RLock
from typing import Any

LOGGER = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
except Exception:
    Elasticsearch = None


class InMemoryStorage:
    def __init__(self) -> None:
        self._lock = RLock()
        self._tables: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def save_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._tables["events"].append(deepcopy(event))
        return deepcopy(event)

    def save_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = [item for item in self._tables["incidents"] if item.get("id") != incident.get("id")]
            rows.append(deepcopy(incident))
            self._tables["incidents"] = rows
        return deepcopy(incident)

    def save_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = [item for item in self._tables["entities"] if item.get("entity_id") != entity.get("entity_id")]
            rows.append(deepcopy(entity))
            self._tables["entities"] = rows
        return deepcopy(entity)

    def query_incidents(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(sorted(self._tables["incidents"], key=lambda item: float(item.get("risk_score", item.get("riskScore", 0.0))), reverse=True))

    def query_events(self, limit: int = 50, query: str = "") -> list[dict[str, Any]]:
        with self._lock:
            rows = deepcopy(self._tables["events"])
        if query:
            q = query.lower()
            rows = [row for row in rows if q in str(row.get("user", "")).lower() or q in str(row.get("host", "")).lower() or q in str(row.get("action", row.get("event_type", ""))).lower()]
        return list(sorted(rows, key=lambda item: item.get("timestamp", ""), reverse=True))[:limit]

    def aggregate_metrics(self) -> dict[str, Any]:
        incidents = self.query_incidents()
        events = self.query_events(limit=200)
        severity_distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for incident in incidents:
            level = str(incident.get("severity", "Medium")).title()
            severity_distribution[level] = severity_distribution.get(level, 0) + 1
        return {
            "logs_indexed": len(events),
            "incidents_indexed": len(incidents),
            "severity_distribution": severity_distribution,
            "risk_distribution": [float(item.get("risk_score", item.get("riskScore", 0.0))) for item in incidents[:20]],
            "recent_activity": events[:10],
        }


class ElasticsearchStorage:
    INDEX_LOGS = "trustsphere_logs"
    INDEX_INCIDENTS = "trustsphere_incidents"
    INDEX_ENTITIES = "trustsphere_entities"

    def __init__(self, host: str = "http://127.0.0.1:9200") -> None:
        if Elasticsearch is None:
            raise RuntimeError("Elasticsearch client unavailable")
        self.client = Elasticsearch(hosts=[host])
        if not self.client.ping():
            raise RuntimeError("Elasticsearch host unreachable")
        self._ensure_indices()

    def _ensure_indices(self) -> None:
        definitions = {
            self.INDEX_LOGS: {"properties": {"timestamp": {"type": "date"}, "user": {"type": "keyword"}, "host": {"type": "keyword"}, "ip": {"type": "keyword"}, "action": {"type": "keyword"}, "severity": {"type": "keyword"}}},
            self.INDEX_INCIDENTS: {"properties": {"id": {"type": "keyword"}, "severity": {"type": "keyword"}, "status": {"type": "keyword"}, "risk_score": {"type": "float"}}},
            self.INDEX_ENTITIES: {"properties": {"entity_id": {"type": "keyword"}, "entity_type": {"type": "keyword"}, "risk_score": {"type": "float"}}},
        }
        for index_name, mapping in definitions.items():
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, mappings=mapping)

    def save_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.client.index(index=self.INDEX_LOGS, document=event)
        return deepcopy(event)

    def save_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        self.client.index(index=self.INDEX_INCIDENTS, id=incident.get("id"), document=incident)
        return deepcopy(incident)

    def save_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        self.client.index(index=self.INDEX_ENTITIES, id=entity.get("entity_id"), document=entity)
        return deepcopy(entity)

    def query_incidents(self) -> list[dict[str, Any]]:
        results = self.client.search(index=self.INDEX_INCIDENTS, query={"match_all": {}}, size=200)
        return [hit["_source"] for hit in results.get("hits", {}).get("hits", [])]

    def query_events(self, limit: int = 50, query: str = "") -> list[dict[str, Any]]:
        body = {"match_all": {}} if not query else {"multi_match": {"query": query, "fields": ["user", "host", "action", "event_type"]}}
        results = self.client.search(index=self.INDEX_LOGS, query=body, size=limit)
        return [hit["_source"] for hit in results.get("hits", {}).get("hits", [])]

    def aggregate_metrics(self) -> dict[str, Any]:
        incidents = self.query_incidents()
        severity_distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for incident in incidents:
            level = str(incident.get("severity", "Medium")).title()
            severity_distribution[level] = severity_distribution.get(level, 0) + 1
        return {
            "logs_indexed": len(self.query_events(limit=200)),
            "incidents_indexed": len(incidents),
            "severity_distribution": severity_distribution,
            "risk_distribution": [float(item.get("risk_score", item.get("riskScore", 0.0))) for item in incidents[:20]],
            "recent_activity": self.query_events(limit=10),
        }


class StorageAdapter:
    def __init__(self, host: str = "http://127.0.0.1:9200") -> None:
        self.backend_name = "memory"
        try:
            self.backend = ElasticsearchStorage(host=host)
            self.backend_name = "elasticsearch"
        except Exception as exc:
            LOGGER.warning("[PIPELINE] storage degraded to memory: %s", exc)
            self.backend = InMemoryStorage()
            self.backend_name = "memory"

    def save_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self.backend.save_event(event)

    def save_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        return self.backend.save_incident(incident)

    def save_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        return self.backend.save_entity(entity)

    def query_incidents(self) -> list[dict[str, Any]]:
        return self.backend.query_incidents()

    def query_events(self, limit: int = 50, query: str = "") -> list[dict[str, Any]]:
        return self.backend.query_events(limit=limit, query=query)

    def aggregate_metrics(self) -> dict[str, Any]:
        return self.backend.aggregate_metrics()
