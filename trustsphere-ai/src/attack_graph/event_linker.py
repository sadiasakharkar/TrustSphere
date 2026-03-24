"""Event linking rules for TrustSphere attack graph reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class LinkConfig:
    """Configuration for temporal event linking."""

    same_user_hours: int = 2
    anomaly_increase_threshold: float = 0.05


class EventLinker:
    """Link security events into directed behavioral relationships."""

    def __init__(self, config: LinkConfig | None = None) -> None:
        self.config = config or LinkConfig()

    def link_events(self, events_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Create directed relations between temporally consistent events."""
        frame = self._prepare_events(events_df)
        linked_events: list[dict[str, Any]] = []

        for _, user_events in frame.groupby("user", sort=False):
            user_events = user_events.sort_values("timestamp").reset_index(drop=True)
            linked_events.extend(self._link_user_sequence(user_events))

        LOGGER.info("Linked relations generated: %s", len(linked_events))
        return linked_events

    def _prepare_events(self, events_df: pd.DataFrame) -> pd.DataFrame:
        frame = events_df.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        required = {"timestamp", "user", "host", "event_type"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns for event linking: {sorted(missing)}")

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=False)
        frame = frame.dropna(subset=["timestamp", "user", "host", "event_type"]).copy()
        frame["user"] = frame["user"].astype(str).str.strip().str.lower()
        frame["host"] = frame["host"].astype(str).str.strip().str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.strip().str.lower()
        frame["ip"] = frame.get("ip", frame.get("ip_address", "unknown")).astype(str).str.strip().str.lower()
        frame["risk_level"] = frame.get("risk_level", "LOW").astype(str).str.upper()
        frame["anomaly_score"] = pd.to_numeric(frame.get("anomaly_score", 0.0), errors="coerce").fillna(0.0)
        frame["event_id"] = frame.get("event_id", frame.index.map(lambda idx: f"evt-{idx:06d}"))
        frame = frame.sort_values(["user", "timestamp"]).reset_index(drop=True)
        return frame

    def _link_user_sequence(self, user_events: pd.DataFrame) -> list[dict[str, Any]]:
        linked_events: list[dict[str, Any]] = []
        for index in range(1, len(user_events)):
            previous_row = user_events.iloc[index - 1]
            current_row = user_events.iloc[index]
            time_delta_hours = (current_row["timestamp"] - previous_row["timestamp"]).total_seconds() / 3600.0
            if time_delta_hours < 0 or time_delta_hours > self.config.same_user_hours:
                continue

            relation_type, why_linked, confidence = self._determine_relation(previous_row, current_row)
            if relation_type is None:
                continue

            linked_events.append(
                {
                    "source_event_id": previous_row["event_id"],
                    "target_event_id": current_row["event_id"],
                    "source_user": current_row["user"],
                    "target_user": current_row["user"],
                    "relation_type": relation_type,
                    "time_delta_hours": round(time_delta_hours, 4),
                    "confidence_score": round(confidence, 4),
                    "why_linked": why_linked,
                    "risk_reason": self._build_risk_reason(previous_row, current_row, relation_type),
                }
            )
        return linked_events

    def _determine_relation(self, previous_row: pd.Series, current_row: pd.Series) -> tuple[str | None, str, float]:
        previous_event = str(previous_row["event_type"])
        current_event = str(current_row["event_type"])
        relation_type = None
        why_linked = ""
        confidence = 0.55

        if previous_event in {"login_success", "logon", "login"} and current_event in {"privilege_change", "admin_action"}:
            relation_type = "privilege_escalation"
            why_linked = "Successful authentication followed by privileged activity."
            confidence = 0.92
        elif previous_row["host"] != current_row["host"]:
            relation_type = "device_pivot"
            why_linked = "Same user shifted activity to a different host within a short interval."
            confidence = 0.85
        elif previous_row["ip"] != current_row["ip"]:
            relation_type = "ip_switch"
            why_linked = "Same user changed source IP quickly, suggesting pivoting or lateral movement."
            confidence = 0.88
        elif float(current_row["anomaly_score"]) - float(previous_row["anomaly_score"]) >= self.config.anomaly_increase_threshold:
            relation_type = "suspicious_escalation"
            why_linked = "Anomaly score increased across a continuous user activity chain."
            confidence = 0.78
        else:
            relation_type = "same_user_sequence"
            why_linked = "Chronological same-user activity within the enterprise continuity window."
            confidence = 0.62

        return relation_type, why_linked, confidence

    def _build_risk_reason(self, previous_row: pd.Series, current_row: pd.Series, relation_type: str) -> str:
        if relation_type == "privilege_escalation":
            return "Potential privilege escalation sequence detected."
        if relation_type == "device_pivot":
            return "Host pivot may indicate compromised credentials or session hijacking."
        if relation_type == "ip_switch":
            return "Rapid IP switching may represent lateral movement or impossible travel."
        if relation_type == "suspicious_escalation":
            return "Anomaly trajectory is increasing over time."
        return f"Sequential activity continuity observed for user {current_row['user']}."
