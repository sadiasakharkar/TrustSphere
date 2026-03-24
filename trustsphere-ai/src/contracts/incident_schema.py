"""Versioned incident and attack graph schemas for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .anomaly_schema import AnomalyResult
from .feature_schema import FeatureMatrix
from .risk_schema import RiskResult

INCIDENT_SCHEMA_VERSION = "incident.v1"


class AttackGraphNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
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

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
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

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
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

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
    nodes: list[AttackGraphNode]
    edges: list[AttackGraphEdge]
    chains: list[AttackChain]
    critical_chains: int = 0


class IncidentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
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
