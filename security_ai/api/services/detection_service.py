from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

from security_ai.api.model_loader import ModelLoader
from security_ai.api.ml_runtime.safe_import import ML_AVAILABLE, simulate_anomaly_score

BASE_DIR = Path(__file__).resolve().parents[3]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"
import sys
if str(TRUSTSPHERE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(TRUSTSPHERE_AI_DIR))

from src.pipeline.event_normalizer import EventNormalizer


class DetectionService:
    def __init__(self, loader: ModelLoader | None = None) -> None:
        self.loader = loader or ModelLoader.get_instance()
        self.normalizer = EventNormalizer()
        self._pipeline = None

    def _get_pipeline(self) -> UEBAInferencePipeline | None:
        if not ML_AVAILABLE:
            return None
        if self._pipeline is not None:
            return self._pipeline
        try:
            import pandas as pd  # noqa: F401
            from src.models.inference_pipeline import UEBAInferencePipeline
            self._pipeline = UEBAInferencePipeline(TRUSTSPHERE_AI_DIR / "saved_models")
        except Exception as exc:
            LOGGER.warning("UEBA inference pipeline unavailable, using heuristic detection fallback: %s", exc)
            self._pipeline = None
        return self._pipeline

    def detect(self, raw_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = self.normalizer.normalize(raw_logs)
        pipeline = self._get_pipeline()
        if pipeline is None:
            return [self._heuristic_result(event.model_dump(mode="json")) for event in normalized]

        import pandas as pd
        frame = pd.DataFrame([event.model_dump(mode="python") for event in normalized])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.tz_convert(None)
        frame["user"] = frame["user"].astype(str).str.lower()
        frame["host"] = frame["host"].astype(str).str.lower()
        frame["ip"] = frame["ip"].astype(str).str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.lower()
        frame["status"] = frame["status"].astype(str).str.lower()
        frame["process_name"] = frame["process_name"].astype(str).str.lower()
        frame["entity_id"] = frame["user"].fillna(frame["host"])
        frame["event_id"] = frame["event_id"].where(frame["event_id"].notna(), [f"evt-{index:06d}" for index in range(len(frame))])

        try:
            predictions = pipeline.predict(frame)
        except Exception as exc:
            LOGGER.warning("UEBA detection failed, using heuristic fallback: %s", exc)
            return [self._heuristic_result(event.model_dump(mode="json")) for event in normalized]

        results: list[dict[str, Any]] = []
        for _, row in predictions.iterrows():
            action = str(row.get("event_type", "unknown"))
            anomaly_score = float(row.get("anomaly_score", 0.0))
            results.append({
                "entity_id": str(row.get("entity_id", "unknown-entity")),
                "timestamp": pd.to_datetime(row.get("timestamp"), utc=True).isoformat() if row.get("timestamp") is not None else datetime.now(timezone.utc).isoformat(),
                "anomaly_score": anomaly_score,
                "feature_importance": self._feature_importance_for_action(action, row.to_dict()),
                "deviation_reason": self._reason_for_action(action, row.to_dict()),
                "event_id": str(row.get("event_id", "")),
                "source": "isolation_forest_tsfresh",
            })
        return results

    def _heuristic_result(self, event: dict[str, Any]) -> dict[str, Any]:
        reason = self._reason_for_action(str(event.get("event_type", "unknown")), event)
        score = 0.35
        simulated = simulate_anomaly_score(event)
        score = max(score, simulated)
        if not event.get("login_success", True):
            score += 0.18
        if float(event.get("bytes_sent", 0.0) or 0.0) > 500000:
            score += 0.2
        if int(event.get("failed_attempts", 0) or 0) >= 5:
            score += 0.15
        if "privilege" in str(event.get("event_type", "")).lower():
            score += 0.18
        score = max(0.01, min(score, 0.99))
        return {
            "entity_id": event.get("user") or event.get("host") or "unknown-entity",
            "timestamp": event.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "anomaly_score": round(score, 4),
            "feature_importance": self._feature_importance_for_action(str(event.get("event_type", "unknown")), event),
            "deviation_reason": reason,
            "event_id": event.get("event_id") or "heuristic-event",
            "source": "heuristic_fallback",
        }

    def _feature_importance_for_action(self, action: str, payload: dict[str, Any]) -> dict[str, float]:
        return {
            "failed_attempts": float(payload.get("failed_attempts", 0) or 0),
            "bytes_sent": round(min(float(payload.get("bytes_sent", 0.0) or 0.0) / 1000000.0, 1.0), 4),
            "privilege_indicator": 1.0 if "privilege" in action or "admin" in action else 0.2,
            "status_failure": 1.0 if str(payload.get("status", "")).lower() in {"failed", "error", "denied"} else 0.0,
        }

    def _reason_for_action(self, action: str, payload: dict[str, Any]) -> str:
        action_lower = action.lower()
        if "login" in action_lower and int(payload.get("failed_attempts", 0) or 0) >= 5:
            return "Repeated login failures deviated from the entity baseline."
        if "privilege" in action_lower or "admin" in action_lower:
            return "Privileged activity was observed outside the normal maintenance baseline."
        if float(payload.get("bytes_sent", 0.0) or 0.0) > 500000:
            return "Outbound data volume exceeded the recent entity baseline."
        return "Behavioral sequence deviated from historical entity activity."
