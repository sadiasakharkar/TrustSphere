"""Versioned detector output contracts for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DETECTOR_SCHEMA_VERSION = "detector.v1"


class DetectorFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[DETECTOR_SCHEMA_VERSION] = DETECTOR_SCHEMA_VERSION
    detector_name: str
    entity_id: str
    timestamp: datetime
    finding_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    raw_output: dict[str, Any] = Field(default_factory=dict)


class DetectorFindingBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[DETECTOR_SCHEMA_VERSION] = DETECTOR_SCHEMA_VERSION
    findings: list[DetectorFinding] = Field(default_factory=list)
