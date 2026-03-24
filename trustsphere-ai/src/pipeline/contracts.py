"""Shared Pydantic contracts for the TrustSphere intelligence engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NormalizedLog(BaseModel):
    """Canonical normalized security event consumed by the intelligence engine."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

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


class FeatureRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    timestamp: datetime
    features: dict[str, float]


class FeatureMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[FeatureRow]
    feature_columns: list[str]


class AnomalyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    timestamp: datetime
    anomaly_score: float
    anomaly_label: int


class RiskResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    timestamp: datetime
    anomaly_score: float
    risk_score: float
    risk_level: str
    behavioral_risk: float
    historical_risk: float


class AttackGraphNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    node_type: str | None = None
    entity_id: str | None = None
    event_id: str | None = None
    timestamp: str | None = None
    event_type: str | None = None
    user: str | None = None
    host: str | None = None
    ip: str | None = None
    process: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    anomaly_score: float | None = None
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    mitre_id: str | None = None


class AttackGraphEdge(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    edge_key: int | str | None = None
    relation_type: str | None = None
    timestamp: str | None = None
    time_delta_minutes: float | None = None
    confidence_score: float | None = None
    why_linked: str | None = None
    risk_reason: str | None = None


class AttackChain(BaseModel):
    model_config = ConfigDict(extra="allow")

    attack_chain_id: str
    sequence_of_events: list[dict[str, Any]]
    entities_involved: list[str]
    start_time: str | None = None
    end_time: str | None = None
    path_length: int | None = None
    anomaly_density: float | None = None
    risk_propagation: float | None = None
    chain_relations: list[dict[str, Any]] = Field(default_factory=list)
    risk_score: float | None = None
    severity: str | None = None
    mitre_tags: list[str] = Field(default_factory=list)


class AttackGraphResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[AttackGraphNode]
    edges: list[AttackGraphEdge]
    chains: list[AttackChain]
    critical_chains: int = 0


class IncidentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    timestamp: datetime
    severity: str
    confidence: str
    anomaly_results: list[AnomalyResult]
    risk_results: list[RiskResult]
    feature_matrix: FeatureMatrix
    attack_graph: AttackGraphResult
    incident_summary: dict[str, Any]
    soc_dashboard: dict[str, Any]
    incident_report_path: str
    response_playbook_path: str
