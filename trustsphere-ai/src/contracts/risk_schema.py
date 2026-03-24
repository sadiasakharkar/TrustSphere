"""Versioned UEBA risk schemas for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

RISK_SCHEMA_VERSION = "risk.v1"


class RiskResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[RISK_SCHEMA_VERSION] = RISK_SCHEMA_VERSION
    entity_id: str
    timestamp: datetime
    anomaly_score: float
    risk_score: float
    risk_level: str
    behavioral_risk: float
    historical_risk: float
