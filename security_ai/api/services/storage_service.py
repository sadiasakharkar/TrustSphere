from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any

from security_ai.api.storage.adapter import StorageAdapter

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
        self.adapter = StorageAdapter(host=host)

    @property
    def backend(self) -> str:
        return self.adapter.backend_name

    def _ensure_indices(self) -> None:
        return None

    def index_normalized_logs(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock:
            for event in events:
                row = deepcopy(event)
                row.setdefault("indexed_at", datetime.now(timezone.utc).isoformat())
                self.adapter.save_event(row)
            return deepcopy(events)

    def index_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = deepcopy(incident)
            row.setdefault("indexed_at", datetime.now(timezone.utc).isoformat())
            return self.adapter.save_incident(row)

    def index_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = deepcopy(entity)
            return self.adapter.save_entity(row)

    def fetch_incidents(self) -> list[dict[str, Any]]:
        return self.adapter.query_incidents()

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        for item in self.adapter.query_incidents():
            if item.get("id") == incident_id:
                return deepcopy(item)
        return None

    def query_alerts(self, *, limit: int = 50, query: str = "") -> list[dict[str, Any]]:
        return self.adapter.query_events(limit=limit, query=query)

    def aggregate_metrics(self) -> dict[str, Any]:
        return {
            "storage_backend": self.backend,
            **self.adapter.aggregate_metrics(),
        }
