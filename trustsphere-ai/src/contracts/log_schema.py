"""Versioned log input schemas for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LOG_SCHEMA_VERSION = "log.v1"


class NormalizedLog(BaseModel):
    """Canonical normalized security event consumed by the intelligence engine."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal[LOG_SCHEMA_VERSION] = LOG_SCHEMA_VERSION
    timestamp: datetime
    user: str = Field(min_length=1)
    host: str = Field(min_length=1)
    ip: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    status: str = Field(default="unknown")
    device_type: str = Field(default="unknown")
    location: str = Field(default="unknown")
    process_name: str = Field(default="unknown-process")
    failed_attempts: int = Field(default=0, ge=0)
    bytes_sent: float = Field(default=0.0, ge=0.0)
    bytes_received: float = Field(default=0.0, ge=0.0)
    login_success: bool | None = None
    event_id: str | None = None
