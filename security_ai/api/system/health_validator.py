from __future__ import annotations

from typing import Any

from security_ai.api.ml_runtime.safe_import import check_ml_runtime
from security_ai.api.pipeline.execution_mode import ExecutionReadiness, HYBRID_MODE, LIVE_MODE, SIMULATION_MODE, select_execution_mode


class HealthValidator:
    def __init__(self, *, storage_backend: str, ollama_health: dict[str, Any], websocket_enabled: bool = True) -> None:
        self.storage_backend = storage_backend
        self.ollama_health = ollama_health
        self.websocket_enabled = websocket_enabled

    def check_ml_runtime(self) -> bool:
        return bool(check_ml_runtime()["available"])

    def check_ollama(self) -> bool:
        return bool(self.ollama_health.get("service_reachable") and self.ollama_health.get("model_available"))

    def check_elasticsearch(self) -> bool:
        return self.storage_backend == "elasticsearch"

    def check_websocket(self) -> bool:
        return self.websocket_enabled

    def check_pipeline_ready(self) -> dict[str, Any]:
        readiness = ExecutionReadiness(
            ml_runtime=self.check_ml_runtime(),
            ollama=self.check_ollama(),
            elasticsearch=self.check_elasticsearch(),
        )
        mode = select_execution_mode(readiness)
        degraded = mode != LIVE_MODE
        return {
            "pipeline": "ready" if mode in {LIVE_MODE, HYBRID_MODE} else "degraded",
            "pipeline_mode": mode,
            "ml_runtime": readiness.ml_runtime,
            "ollama": readiness.ollama,
            "elasticsearch": readiness.elasticsearch,
            "websocket": self.check_websocket(),
            "fallback_mode": degraded,
        }
