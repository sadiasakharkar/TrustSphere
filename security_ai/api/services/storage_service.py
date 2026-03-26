from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any

LOGGER = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
except Exception:
    Elasticsearch = None


class StorageService:
    INDEX_LOGS = "trustsphere_logs"
    INDEX_INCIDENTS = "trustsphere_incidents"
    INDEX_ENTITIES = "trustsphere_entities"

    def __init__(self, host: str = "http://127.0.0.1:9200") -> None:
        self.host = host
        self._lock = RLock()
        self._memory_indices: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._client = None
        if Elasticsearch is not None:
            try:
                client = Elasticsearch(hosts=[host])
                if client.ping():
                    self._client = client
                    self._ensure_indices()
            except Exception as exc:
                LOGGER.warning("Elasticsearch unavailable, falling back to in-memory storage: %s", exc)
                self._client = None

    @property
    def backend(self) -> str:
        return "elasticsearch" if self._client is not None else "memory"

    def _ensure_indices(self) -> None:
        assert self._client is not None
        mappings = {
            self.INDEX_LOGS: {"properties": {"timestamp": {"type": "date"}, "user": {"type": "keyword"}, "host": {"type": "keyword"}, "ip": {"type": "ip"}, "action": {"type": "keyword"}, "severity": {"type": "keyword"}}},
            self.INDEX_INCIDENTS: {"properties": {"id": {"type": "keyword"}, "severity": {"type": "keyword"}, "status": {"type": "keyword"}, "risk_score": {"type": "float"}, "created_at": {"type": "date"}}},
            self.INDEX_ENTITIES: {"properties": {"entity_id": {"type": "keyword"}, "entity_type": {"type": "keyword"}, "risk_score": {"type": "float"}}},
        }
        for index_name, body in mappings.items():
            if not self._client.indices.exists(index=index_name):
                self._client.indices.create(index=index_name, mappings=body["properties"] and body)

    def index_normalized_logs(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock:
            for event in events:
                row = deepcopy(event)
                row.setdefault("indexed_at", datetime.now(timezone.utc).isoformat())
                if self._client is not None:
                    self._client.index(index=self.INDEX_LOGS, document=row)
                self._memory_indices[self.INDEX_LOGS].append(row)
            return deepcopy(events)

    def index_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = deepcopy(incident)
            row.setdefault("indexed_at", datetime.now(timezone.utc).isoformat())
            if self._client is not None:
                self._client.index(index=self.INDEX_INCIDENTS, id=row.get("id"), document=row)
            existing = [item for item in self._memory_indices[self.INDEX_INCIDENTS] if item.get("id") != row.get("id")]
            existing.append(row)
            self._memory_indices[self.INDEX_INCIDENTS] = existing
            return deepcopy(row)

    def index_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = deepcopy(entity)
            if self._client is not None:
                self._client.index(index=self.INDEX_ENTITIES, id=row.get("entity_id"), document=row)
            existing = [item for item in self._memory_indices[self.INDEX_ENTITIES] if item.get("entity_id") != row.get("entity_id")]
            existing.append(row)
            self._memory_indices[self.INDEX_ENTITIES] = existing
            return deepcopy(row)

    def fetch_incidents(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = deepcopy(self._memory_indices[self.INDEX_INCIDENTS])
        return sorted(rows, key=lambda item: float(item.get("risk_score", item.get("riskScore", 0.0))), reverse=True)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with self._lock:
            for item in self._memory_indices[self.INDEX_INCIDENTS]:
                if item.get("id") == incident_id:
                    return deepcopy(item)
        return None

    def query_alerts(self, *, limit: int = 50, query: str = "") -> list[dict[str, Any]]:
        with self._lock:
            rows = deepcopy(self._memory_indices[self.INDEX_LOGS])
        if query:
            q = query.lower()
            rows = [row for row in rows if q in str(row.get("user", "")).lower() or q in str(row.get("host", "")).lower() or q in str(row.get("action", "")).lower()]
        return list(sorted(rows, key=lambda item: item.get("timestamp", ""), reverse=True))[:limit]

    def aggregate_metrics(self) -> dict[str, Any]:
        incidents = self.fetch_incidents()
        alerts = self.query_alerts(limit=200)
        severity_distribution: dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for incident in incidents:
            severity = str(incident.get("severity", "Medium")).title()
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        return {
            "storage_backend": self.backend,
            "logs_indexed": len(alerts),
            "incidents_indexed": len(incidents),
            "severity_distribution": severity_distribution,
            "risk_distribution": [float(item.get("risk_score", item.get("riskScore", 0.0))) for item in incidents[:20]],
            "recent_activity": alerts[:10],
        }
