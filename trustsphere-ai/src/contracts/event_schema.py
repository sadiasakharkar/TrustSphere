"""Canonical normalized event contract for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EVENT_SCHEMA_VERSION = "event.v1"


class NormalizedEvent(BaseModel):
    """Single canonical event schema consumed by all intelligence subsystems."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal[EVENT_SCHEMA_VERSION] = EVENT_SCHEMA_VERSION
    timestamp: datetime
    event_id: str | None = None
    session_id: str | None = None
    user: str = Field(min_length=1)
    host: str = Field(min_length=1)
    ip: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    status: str = Field(default="unknown")
    role: str | None = None
    department: str | None = None
    device_type: str = Field(default="unknown")
    location: str = Field(default="unknown")
    process_name: str = Field(default="unknown-process")
    event_category: str | None = None
    event_source: str | None = None
    severity_hint: str | None = None
    risk_hint: str | None = None
    failed_attempts: int = Field(default=0, ge=0)
    bytes_sent: float = Field(default=0.0, ge=0.0)
    bytes_received: float = Field(default=0.0, ge=0.0)
    login_success: bool | None = None
    label: str | None = None

    email_subject: str | None = None
    email_body: str | None = None
    sender: str | None = None
    url: str | None = None
    text_content: str | None = None
    attachment_name: str | None = None
    attachment_size_bytes: int | None = Field(default=None, ge=0)
    post_download_action: str | None = None
    prompt_text: str | None = None

    raw_payload: dict[str, Any] = Field(default_factory=dict)
