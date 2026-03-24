"""Versioned anomaly schemas for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ANOMALY_SCHEMA_VERSION = "anomaly.v1"


class AnomalyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[ANOMALY_SCHEMA_VERSION] = ANOMALY_SCHEMA_VERSION
    entity_id: str
    timestamp: datetime
    anomaly_score: float
    anomaly_label: int
