"""Canonical event normalization for TrustSphere unified orchestration."""

from __future__ import annotations

from typing import Any

from ..contracts import EVENT_SCHEMA_VERSION, NormalizedEvent


class EventNormalizer:
    """Map raw events into the canonical NormalizedEvent contract."""

    FIELD_ALIASES = {
        "host": ["host", "device", "device_name", "hostname"],
        "ip": ["ip", "ip_address", "source_ip"],
        "process_name": ["process_name", "process", "command"],
        "device_type": ["device_type", "device_kind"],
        "status": ["status", "result", "outcome"],
        "location": ["location", "geo", "city", "baseline_location"],
        "department": ["department", "team"],
        "role": ["role"],
        "event_source": ["event_source", "source"],
        "event_category": ["event_category", "category"],
        "email_subject": ["email_subject", "subject"],
        "email_body": ["email_body", "body"],
        "sender": ["sender", "from_address"],
        "url": ["url", "link", "uri"],
        "text_content": ["text_content", "text", "content_text", "payload_text"],
        "attachment_name": ["attachment_name", "filename"],
        "attachment_size_bytes": ["attachment_size_bytes", "size_bytes"],
        "post_download_action": ["post_download_action", "event_context"],
        "prompt_text": ["prompt_text", "prompt"],
        "session_id": ["session_id"],
        "event_id": ["event_id"],
        "severity_hint": ["severity_hint"],
        "risk_hint": ["risk_hint"],
        "label": ["label"],
        "failed_attempts": ["failed_attempts"],
        "bytes_sent": ["bytes_sent"],
        "bytes_received": ["bytes_received"],
        "login_success": ["login_success"],
    }

    def normalize(self, raw_input: list[dict[str, Any]] | list[NormalizedEvent] | dict[str, Any] | NormalizedEvent) -> list[NormalizedEvent]:
        if isinstance(raw_input, NormalizedEvent):
            return [raw_input]
        if isinstance(raw_input, dict):
            raw_events = [raw_input]
        else:
            raw_events = list(raw_input)
        normalized = []
        for raw in raw_events:
            if isinstance(raw, NormalizedEvent):
                normalized.append(raw)
                continue
            normalized.append(self._normalize_one(raw))
        return normalized

    def _normalize_one(self, raw: dict[str, Any]) -> NormalizedEvent:
        event = {
            "schema_version": raw.get("schema_version", EVENT_SCHEMA_VERSION),
            "timestamp": raw.get("timestamp"),
            "event_id": self._pick(raw, "event_id"),
            "session_id": self._pick(raw, "session_id"),
            "user": str(raw.get("user", raw.get("user_id", "unknown-user"))),
            "host": str(self._pick(raw, "host", default="unknown-host")),
            "ip": str(self._pick(raw, "ip", default="0.0.0.0")),
            "event_type": str(raw.get("event_type", "unknown_event")),
            "status": str(self._pick(raw, "status", default="unknown")),
            "role": self._pick(raw, "role"),
            "department": self._pick(raw, "department"),
            "device_type": str(self._pick(raw, "device_type", default="unknown")),
            "location": str(self._pick(raw, "location", default="unknown")),
            "process_name": str(self._pick(raw, "process_name", default="unknown-process")),
            "event_category": self._pick(raw, "event_category"),
            "event_source": self._pick(raw, "event_source"),
            "severity_hint": self._pick(raw, "severity_hint"),
            "risk_hint": self._pick(raw, "risk_hint"),
            "failed_attempts": int(self._pick(raw, "failed_attempts", default=0) or 0),
            "bytes_sent": float(self._pick(raw, "bytes_sent", default=0.0) or 0.0),
            "bytes_received": float(self._pick(raw, "bytes_received", default=0.0) or 0.0),
            "login_success": self._pick(raw, "login_success"),
            "label": self._pick(raw, "label"),
            "email_subject": self._pick(raw, "email_subject"),
            "email_body": self._pick(raw, "email_body"),
            "sender": self._pick(raw, "sender"),
            "url": self._pick(raw, "url"),
            "text_content": self._pick(raw, "text_content"),
            "attachment_name": self._pick(raw, "attachment_name"),
            "attachment_size_bytes": self._coerce_optional_int(self._pick(raw, "attachment_size_bytes")),
            "post_download_action": self._pick(raw, "post_download_action"),
            "prompt_text": self._pick(raw, "prompt_text"),
            "raw_payload": dict(raw),
        }
        return NormalizedEvent.model_validate(event)

    def _pick(self, raw: dict[str, Any], canonical_field: str, default: Any = None) -> Any:
        for key in self.FIELD_ALIASES.get(canonical_field, [canonical_field]):
            if key in raw and raw[key] is not None:
                return raw[key]
        return default

    def _coerce_optional_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)
