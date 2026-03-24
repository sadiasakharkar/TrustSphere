"""Unified orchestration output contract for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .detector_schema import DetectorFindingBatch
from .event_schema import NormalizedEvent
from .incident_schema import IncidentReport
from .risk_schema import RiskResult
from .anomaly_schema import AnomalyResult
from .feature_schema import FeatureMatrix
from .graph_schema import AttackGraphResult

UNIFIED_OUTPUT_SCHEMA_VERSION = "unified_output.v1"


class UnifiedIncidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[UNIFIED_OUTPUT_SCHEMA_VERSION] = UNIFIED_OUTPUT_SCHEMA_VERSION
    generated_at: datetime
    execution_mode: str
    normalized_events: list[NormalizedEvent]
    feature_matrix: FeatureMatrix
    detector_findings: DetectorFindingBatch
    anomaly_results: list[AnomalyResult]
    risk_results: list[RiskResult]
    attack_graph: AttackGraphResult
    incident_report: IncidentReport
    execution_metadata: dict[str, Any] = Field(default_factory=dict)
