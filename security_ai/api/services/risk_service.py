from __future__ import annotations

from collections import Counter
from typing import Any


class RiskService:
    def __init__(self) -> None:
        self.asset_criticality = {
            "domain_controller": 1.5,
            "database": 1.45,
            "server": 1.3,
            "workstation": 1.0,
            "mail": 1.15,
        }
        self.threat_weights = {
            "login": 1.0,
            "credential": 1.15,
            "privilege": 1.25,
            "lateral": 1.35,
            "exfiltration": 1.5,
            "phishing": 1.05,
        }

    def score(self, detection: dict[str, Any], history: list[dict[str, Any]] | None = None, asset_type: str = "workstation") -> dict[str, Any]:
        history = history or []
        anomaly = float(detection.get("anomaly_score", 0.0))
        behavior = self._behavior_score(detection)
        asset_criticality = self.asset_criticality.get(asset_type, 1.0)
        threat_weight = self._threat_weight(detection)
        frequency_factor = self._frequency_factor(detection, history)
        final_risk = anomaly * behavior * asset_criticality * threat_weight * frequency_factor
        bounded_risk = round(min(max(final_risk * 100.0, 1.0), 99.0), 2)
        severity = self._severity_for_score(bounded_risk)
        return {
            "entity_id": detection.get("entity_id", "unknown-entity"),
            "anomaly_score": anomaly,
            "behavior_score": round(behavior, 4),
            "asset_criticality": asset_criticality,
            "threat_weight": threat_weight,
            "frequency_factor": frequency_factor,
            "risk_score": bounded_risk,
            "severity": severity,
        }

    def _behavior_score(self, detection: dict[str, Any]) -> float:
        importance = detection.get("feature_importance", {}) or {}
        components = [
            min(float(importance.get("failed_attempts", 0.0)) / 10.0, 1.0),
            float(importance.get("bytes_sent", 0.0) or 0.0),
            float(importance.get("privilege_indicator", 0.0) or 0.0),
            float(importance.get("status_failure", 0.0) or 0.0),
        ]
        score = 0.6 + (sum(components) / max(len(components), 1))
        return round(min(score, 1.6), 4)

    def _threat_weight(self, detection: dict[str, Any]) -> float:
        reason = str(detection.get("deviation_reason", "")).lower()
        for key, value in self.threat_weights.items():
            if key in reason:
                return value
        return 1.0

    def _frequency_factor(self, detection: dict[str, Any], history: list[dict[str, Any]]) -> float:
        entity = detection.get("entity_id")
        count = Counter(item.get("entity_id") for item in history)[entity]
        return round(min(1.0 + (count * 0.08), 1.5), 4)

    def _severity_for_score(self, score: float) -> str:
        if score >= 85:
            return "CRITICAL"
        if score >= 65:
            return "HIGH"
        if score >= 35:
            return "MEDIUM"
        return "LOW"
