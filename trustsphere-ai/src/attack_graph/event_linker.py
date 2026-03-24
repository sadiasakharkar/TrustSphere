"""Rule-based event linking for TrustSphere attack graph intelligence."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class LinkConfig:
    same_user_minutes: int = 30


class EventLinker:
    """Link UEBA events into temporal relationships for graph reconstruction."""

    def __init__(self, config: LinkConfig | None = None) -> None:
        self.config = config or LinkConfig()

    def link_events(self, events_df: pd.DataFrame) -> list[dict[str, Any]]:
        frame = self._prepare_events(events_df)
        linked_events: list[dict[str, Any]] = []
        linked_events.extend(self._same_user_links(frame))
        linked_events.extend(self._ip_reuse_links(frame))
        linked_events.extend(self._pattern_links(frame))
        deduped = self._dedupe(linked_events)
        LOGGER.info("Linked relations generated: %s", len(deduped))
        return deduped

    def _prepare_events(self, events_df: pd.DataFrame) -> pd.DataFrame:
        frame = events_df.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        required = {"timestamp", "event_type"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns for event linking: {sorted(missing)}")
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).copy()
        frame["user"] = self._series(frame, "user", frame.get("user_id"), "unknown-user").astype(str).str.lower()
        frame["host"] = self._series(frame, "host", frame.get("host_id", frame.get("device_type")), "unknown-host").astype(str).str.lower()
        frame["ip"] = self._series(frame, "ip", frame.get("ip_address"), "0.0.0.0").astype(str).str.lower()
        frame["process"] = self._series(frame, "process", frame.get("process_name", frame.get("command")), "unknown-process").astype(str).str.lower()
        frame["location"] = self._series(frame, "location", None, "unknown").astype(str).str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.lower()
        frame["risk_level"] = self._series(frame, "risk_level", None, "LOW").astype(str).str.upper()
        frame["risk_score"] = pd.to_numeric(self._series(frame, "risk_score", None, 0.0), errors="coerce").fillna(0.0)
        frame["anomaly_score"] = pd.to_numeric(self._series(frame, "anomaly_score", None, 0.0), errors="coerce").fillna(0.0)
        frame["event_id"] = self._series(frame, "event_id", None, None)
        frame["event_id"] = [value if value not in {None, "None", "nan"} else f"evt-{idx:06d}" for idx, value in enumerate(frame["event_id"])]
        return frame.sort_values(["user", "timestamp", "event_id"]).reset_index(drop=True)

    def _same_user_links(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        links: list[dict[str, Any]] = []
        for _, user_events in frame.groupby("user", sort=False):
            user_events = user_events.sort_values("timestamp").reset_index(drop=True)
            for index in range(1, len(user_events)):
                previous = user_events.iloc[index - 1]
                current = user_events.iloc[index]
                delta_minutes = (current["timestamp"] - previous["timestamp"]).total_seconds() / 60.0
                if delta_minutes < 0 or delta_minutes > self.config.same_user_minutes:
                    continue
                relation = "same_user"
                why = "Same user activity occurred within 30 minutes."
                if previous["event_type"] in {"login_success", "login_success_new_ip", "logon", "login"} and current["process"] != "unknown-process":
                    relation = "executed_on"
                    why = "Anomalous or successful login was followed by process execution."
                elif previous["event_type"] in {"privilege_escalation", "privilege_change"} and current["event_type"] == "admin_action":
                    relation = "escalated_to"
                    why = "Privilege escalation was followed by administrative action."
                elif previous["location"] != current["location"] and current["event_type"] in {"file_access", "data_access", "data_exfiltration"}:
                    relation = "connected_to"
                    why = "Geo anomaly was followed by sensitive data access."
                elif previous["host"] != current["host"]:
                    relation = "lateral_move"
                    why = "User activity pivoted across hosts within the correlation window."
                links.append(self._link(previous, current, relation, delta_minutes, why))
        return links

    def _ip_reuse_links(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        links: list[dict[str, Any]] = []
        for _, ip_events in frame.groupby("ip", sort=False):
            ip_events = ip_events.sort_values("timestamp").reset_index(drop=True)
            for index in range(1, len(ip_events)):
                previous = ip_events.iloc[index - 1]
                current = ip_events.iloc[index]
                if previous["host"] == current["host"]:
                    continue
                delta_minutes = (current["timestamp"] - previous["timestamp"]).total_seconds() / 60.0
                if delta_minutes < 0 or delta_minutes > 120:
                    continue
                links.append(
                    self._link(
                        previous,
                        current,
                        "login_from",
                        delta_minutes,
                        "The same source IP was reused across multiple hosts in a short window.",
                    )
                )
        return links

    def _pattern_links(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        links: list[dict[str, Any]] = []
        for _, user_events in frame.groupby("user", sort=False):
            user_events = user_events.sort_values("timestamp").reset_index(drop=True)
            for index in range(1, len(user_events)):
                previous = user_events.iloc[index - 1]
                current = user_events.iloc[index]
                delta_minutes = (current["timestamp"] - previous["timestamp"]).total_seconds() / 60.0
                if delta_minutes < 0 or delta_minutes > 120:
                    continue
                if previous["event_type"] in {"login_failed", "failed_login", "login_success_new_ip"} and current["process"] != "unknown-process":
                    links.append(self._link(previous, current, "executed_on", delta_minutes, "Anomalous login was followed by process execution."))
                if previous["location"] != current["location"] and current["event_type"] in {"file_access", "data_access", "data_exfiltration"}:
                    links.append(self._link(previous, current, "connected_to", delta_minutes, "Geo anomaly was followed by data access activity."))
        return links

    def _link(self, source: pd.Series, target: pd.Series, relation_type: str, delta_minutes: float, why: str) -> dict[str, Any]:
        return {
            "source_event_id": source["event_id"],
            "target_event_id": target["event_id"],
            "relation_type": relation_type,
            "time_delta_minutes": round(delta_minutes, 4),
            "confidence_score": round(self._confidence(source, target, relation_type), 4),
            "why_linked": why,
            "risk_reason": self._risk_reason(source, target, relation_type),
        }

    def _confidence(self, source: pd.Series, target: pd.Series, relation_type: str) -> float:
        base = 0.6
        if relation_type in {"escalated_to", "lateral_move"}:
            base += 0.2
        if float(target.get("anomaly_score", 0.0)) > float(source.get("anomaly_score", 0.0)):
            base += 0.1
        if str(target.get("risk_level", "LOW")).upper() in {"HIGH", "CRITICAL"}:
            base += 0.1
        return min(base, 0.98)

    def _risk_reason(self, source: pd.Series, target: pd.Series, relation_type: str) -> str:
        mapping = {
            "login_from": "IP reuse across hosts may indicate credential sharing or pivoting.",
            "executed_on": "Authentication activity was followed by endpoint process execution.",
            "connected_to": "Location change preceded data access, increasing compromise likelihood.",
            "escalated_to": "Privilege escalation sequence suggests account abuse.",
            "lateral_move": "Cross-host movement suggests lateral traversal.",
            "same_user": "Temporal continuity links the user activity chain.",
        }
        return mapping.get(relation_type, "Correlated enterprise activity observed.")

    def _dedupe(self, links: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        deduped = []
        for link in links:
            key = (link["source_event_id"], link["target_event_id"], link["relation_type"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(link)
        return deduped

    def _series(self, frame: pd.DataFrame, primary: str, secondary: pd.Series | None, default: Any) -> pd.Series:
        if primary in frame.columns:
            return frame[primary]
        if isinstance(secondary, pd.Series):
            return secondary
        return pd.Series([default] * len(frame), index=frame.index)
