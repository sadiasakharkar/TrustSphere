"""Offline UEBA risk engine for TrustSphere.

This module converts anomaly model output into analyst-facing business risk
intelligence suitable for SOC workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from pathlib import Path
from typing import Any

import pandas as pd


LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@dataclass(slots=True)
class RiskEvaluationContext:
    """Per-event context used to build risk intelligence."""

    new_device_detected: bool = False
    impossible_travel_detected: bool = False
    bytes_spike_detected: bool = False
    login_failed_detected: bool = False


class UEBARiskEngine:
    """Convert ML anomaly outputs into weighted enterprise risk decisions."""

    def __init__(self, anomaly_weight: float = 0.6, behavior_weight: float = 0.4) -> None:
        if anomaly_weight < 0 or behavior_weight < 0:
            raise ValueError("Risk weights must be non-negative.")
        total_weight = anomaly_weight + behavior_weight
        if total_weight == 0:
            raise ValueError("At least one risk weight must be greater than zero.")
        self.anomaly_weight = anomaly_weight / total_weight
        self.behavior_weight = behavior_weight / total_weight

    def calculate_risk_score(
        self,
        row: pd.Series,
        context: RiskEvaluationContext | None = None,
        previous_row: pd.Series | None = None,
    ) -> int:
        """Compute a 0-100 risk score from anomaly model output and risk rules."""
        context = context or RiskEvaluationContext()
        ml_score = max(0.0, min(float(row.get("anomaly_score", 0.0)) * 100.0, 100.0))
        behavior_score = self._calculate_behavior_score(row, context, previous_row)
        weighted_score = (self.anomaly_weight * ml_score) + (self.behavior_weight * behavior_score)
        return int(round(max(0.0, min(weighted_score, 100.0))))

    def detect_impossible_travel(
        self,
        current_row: pd.Series,
        previous_row: pd.Series | None,
    ) -> tuple[bool, str | None]:
        """Flag unrealistic location switching inside a short time window."""
        if previous_row is None:
            return False, None
        if str(current_row.get("user_id")) != str(previous_row.get("user_id")):
            return False, None

        current_location = str(current_row.get("location", "")).strip().lower()
        previous_location = str(previous_row.get("location", "")).strip().lower()
        if not current_location or not previous_location or current_location == previous_location:
            return False, None

        current_timestamp = pd.to_datetime(current_row.get("timestamp"), errors="coerce")
        previous_timestamp = pd.to_datetime(previous_row.get("timestamp"), errors="coerce")
        if pd.isna(current_timestamp) or pd.isna(previous_timestamp):
            return False, None

        if abs(current_timestamp - previous_timestamp) <= timedelta(hours=2):
            return True, "Impossible travel behavior observed"
        return False, None

    def assign_risk_level(self, risk_score: int) -> str:
        """Map numeric risk score to analyst-facing severity band."""
        if risk_score < 30:
            return "LOW"
        if risk_score < 60:
            return "MEDIUM"
        if risk_score < 80:
            return "HIGH"
        return "CRITICAL"

    def generate_reasons(
        self,
        row: pd.Series,
        context: RiskEvaluationContext | None = None,
        previous_row: pd.Series | None = None,
    ) -> list[str]:
        """Create deterministic, human-readable explanations for the assigned risk."""
        context = context or RiskEvaluationContext()
        reasons: list[str] = []

        if float(row.get("anomaly_score", 0.0)) >= 0.85:
            reasons.append("Severe deviation from learned baseline behavior")
        elif int(row.get("is_anomaly", 0)) == 1:
            reasons.append("Model flagged user activity as anomalous")

        if int(row.get("failed_attempts", 0)) > 5:
            reasons.append("Multiple failed login attempts detected")
        if context.new_device_detected:
            reasons.append("Login from unfamiliar device")
        if context.bytes_spike_detected:
            reasons.append("Unusual data transfer volume")
        if context.login_failed_detected:
            reasons.append("Authentication failure associated with risky behavior")

        impossible_travel, travel_reason = self.detect_impossible_travel(row, previous_row)
        if impossible_travel and travel_reason is not None:
            reasons.append(travel_reason)

        if not reasons:
            reasons.append("No elevated behavioral risk indicators detected")
        return reasons

    def recommend_action(self, risk_level: str) -> str:
        """Map risk level to SOC-oriented response guidance."""
        action_map = {
            "LOW": "Monitor",
            "MEDIUM": "Require MFA",
            "HIGH": "Temporary account restriction",
            "CRITICAL": "Immediate lock + SOC alert",
        }
        return action_map.get(risk_level, "Monitor")

    def evaluate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluate all events and return an enriched dataframe with business risk output."""
        if df.empty:
            raise ValueError("Input dataframe is empty.")

        required_columns = {
            "user_id",
            "timestamp",
            "anomaly_score",
            "is_anomaly",
            "ip_address",
            "device_type",
            "location",
            "event_type",
            "failed_attempts",
            "bytes_sent",
            "bytes_received",
        }
        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(f"Missing required columns for risk evaluation: {sorted(missing)}")

        dataframe = df.copy()
        dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], errors="coerce")
        dataframe = dataframe.dropna(subset=["timestamp"]).sort_values(["user_id", "timestamp"]).reset_index(drop=True)

        dataframe["risk_score"] = 0
        dataframe["risk_level"] = "LOW"
        dataframe["risk_reasons"] = pd.Series([[] for _ in range(len(dataframe))], dtype="object")
        dataframe["recommended_action"] = ""

        seen_devices: dict[str, set[str]] = {}
        rolling_bytes_mean: dict[str, float] = {}

        for user_id, user_frame in dataframe.groupby("user_id", sort=False):
            previous_row: pd.Series | None = None
            seen_devices.setdefault(str(user_id), set())
            user_indices = user_frame.index.tolist()
            for row_index in user_indices:
                try:
                    row = dataframe.loc[row_index]
                    context = self._build_context(
                        row=row,
                        previous_row=previous_row,
                        seen_devices=seen_devices[str(user_id)],
                        historical_bytes_mean=rolling_bytes_mean.get(str(user_id)),
                    )

                    risk_score = self.calculate_risk_score(row, context=context, previous_row=previous_row)
                    risk_level = self.assign_risk_level(risk_score)
                    reasons = self.generate_reasons(row, context=context, previous_row=previous_row)
                    recommended_action = self.recommend_action(risk_level)

                    dataframe.at[row_index, "risk_score"] = risk_score
                    dataframe.at[row_index, "risk_level"] = risk_level
                    dataframe.at[row_index, "risk_reasons"] = reasons
                    dataframe.at[row_index, "recommended_action"] = recommended_action

                    seen_devices[str(user_id)].add(str(row.get("device_type", "")).strip().lower())
                    total_bytes = float(row.get("bytes_sent", 0)) + float(row.get("bytes_received", 0))
                    rolling_bytes_mean[str(user_id)] = self._update_bytes_baseline(
                        current_mean=rolling_bytes_mean.get(str(user_id)),
                        current_value=total_bytes,
                    )
                    previous_row = row
                except Exception as exc:
                    LOGGER.exception("Risk evaluation failed for user=%s row_index=%s: %s", user_id, row_index, exc)
                    dataframe.at[row_index, "risk_score"] = 0
                    dataframe.at[row_index, "risk_level"] = "LOW"
                    dataframe.at[row_index, "risk_reasons"] = ["Risk evaluation error"]
                    dataframe.at[row_index, "recommended_action"] = "Monitor"

        LOGGER.info("Completed risk evaluation for %s events", len(dataframe))
        return dataframe

    def _calculate_behavior_score(
        self,
        row: pd.Series,
        context: RiskEvaluationContext,
        previous_row: pd.Series | None,
    ) -> float:
        """Apply rule-based security intelligence on top of anomaly scores."""
        score = 0.0
        score += self._rule_failed_attempts(row)
        score += self._rule_new_device(context)
        score += self._rule_location_change(context)
        score += self._rule_bytes_spike(context)
        score += self._rule_login_failure(row, context)
        return min(score, 100.0)

    def _build_context(
        self,
        row: pd.Series,
        previous_row: pd.Series | None,
        seen_devices: set[str],
        historical_bytes_mean: float | None,
    ) -> RiskEvaluationContext:
        """Build per-event context shared across risk rules and explanations."""
        device = str(row.get("device_type", "")).strip().lower()
        total_bytes = float(row.get("bytes_sent", 0)) + float(row.get("bytes_received", 0))
        impossible_travel_detected, _ = self.detect_impossible_travel(row, previous_row)
        login_success_raw = row.get("login_success", 1)
        login_failed_detected = bool(pd.notna(login_success_raw) and int(login_success_raw) == 0)
        bytes_spike_detected = bool(
            historical_bytes_mean is not None and historical_bytes_mean > 0 and total_bytes >= historical_bytes_mean * 3.0
        )
        return RiskEvaluationContext(
            new_device_detected=bool(device and device not in seen_devices),
            impossible_travel_detected=impossible_travel_detected,
            bytes_spike_detected=bytes_spike_detected,
            login_failed_detected=login_failed_detected,
        )

    def _rule_failed_attempts(self, row: pd.Series) -> int:
        return 15 if int(row.get("failed_attempts", 0)) > 5 else 0

    def _rule_new_device(self, context: RiskEvaluationContext) -> int:
        return 20 if context.new_device_detected else 0

    def _rule_location_change(self, context: RiskEvaluationContext) -> int:
        return 25 if context.impossible_travel_detected else 0

    def _rule_bytes_spike(self, context: RiskEvaluationContext) -> int:
        return 15 if context.bytes_spike_detected else 0

    def _rule_login_failure(self, row: pd.Series, context: RiskEvaluationContext) -> int:
        if context.login_failed_detected:
            return 10
        if str(row.get("event_type", "")).strip().lower() in {"login_failed", "brute_force_login"}:
            return 10
        return 0

    def _update_bytes_baseline(self, current_mean: float | None, current_value: float) -> float:
        """Maintain a simple exponential moving average for transfer baseline."""
        if current_mean is None:
            return current_value
        smoothing = 0.2
        return (1 - smoothing) * current_mean + smoothing * current_value


def compute_risk(anomaly_output: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible wrapper for simple single-record usage."""
    engine = UEBARiskEngine()
    frame = pd.DataFrame([anomaly_output])
    evaluated = engine.evaluate_dataframe(frame)
    row = evaluated.iloc[0]
    return {
        "user_id": row.get("user_id"),
        "risk_score": int(row.get("risk_score", 0)),
        "risk_level": row.get("risk_level", "LOW"),
        "reasons": row.get("risk_reasons", []),
        "recommended_action": row.get("recommended_action", "Monitor"),
    }


if __name__ == "__main__":
    engine = UEBARiskEngine()
    input_path = Path("data/processed/model_output.csv")
    output_path = Path("data/processed/risk_output.csv")
    dataset = pd.read_csv(input_path)
    result = engine.evaluate_dataframe(dataset)
    result.to_csv(output_path, index=False)
