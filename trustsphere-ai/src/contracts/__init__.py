"""Versioned schema registry for TrustSphere intelligence contracts."""

from .anomaly_schema import ANOMALY_SCHEMA_VERSION, AnomalyResult
from .detector_schema import DETECTOR_SCHEMA_VERSION, DetectorFinding, DetectorFindingBatch
from .event_schema import EVENT_SCHEMA_VERSION, NormalizedEvent
from .feature_schema import FEATURE_SCHEMA_VERSION, FeatureMatrix, FeatureRow
from .graph_schema import GRAPH_SCHEMA_VERSION
from .incident_schema import (
    INCIDENT_SCHEMA_VERSION,
    AttackChain,
    AttackGraphEdge,
    AttackGraphNode,
    AttackGraphResult,
    IncidentReport,
)
from .log_schema import LOG_SCHEMA_VERSION, NormalizedLog
from .request_schema import (
    ATTACHMENT_REQUEST_SCHEMA_VERSION,
    CREDENTIAL_REQUEST_SCHEMA_VERSION,
    EMAIL_REQUEST_SCHEMA_VERSION,
    PROMPT_GUARD_REQUEST_SCHEMA_VERSION,
    URL_REQUEST_SCHEMA_VERSION,
    AttachmentDetectionRequest,
    CredentialDetectionRequest,
    EmailDetectionRequest,
    IncidentAnalysisRequest,
    PromptGuardRequest,
    URLDetectionRequest,
)
from .risk_schema import RISK_SCHEMA_VERSION, RiskResult
from .unified_output_schema import UNIFIED_OUTPUT_SCHEMA_VERSION, UnifiedIncidentOutput

__all__ = [
    "ANOMALY_SCHEMA_VERSION",
    "ATTACHMENT_REQUEST_SCHEMA_VERSION",
    "CREDENTIAL_REQUEST_SCHEMA_VERSION",
    "DETECTOR_SCHEMA_VERSION",
    "EMAIL_REQUEST_SCHEMA_VERSION",
    "EVENT_SCHEMA_VERSION",
    "FEATURE_SCHEMA_VERSION",
    "GRAPH_SCHEMA_VERSION",
    "INCIDENT_SCHEMA_VERSION",
    "LOG_SCHEMA_VERSION",
    "PROMPT_GUARD_REQUEST_SCHEMA_VERSION",
    "RISK_SCHEMA_VERSION",
    "UNIFIED_OUTPUT_SCHEMA_VERSION",
    "URL_REQUEST_SCHEMA_VERSION",
    "AnomalyResult",
    "AttackChain",
    "AttackGraphEdge",
    "AttackGraphNode",
    "AttackGraphResult",
    "AttachmentDetectionRequest",
    "CredentialDetectionRequest",
    "DetectorFinding",
    "DetectorFindingBatch",
    "EmailDetectionRequest",
    "FeatureMatrix",
    "FeatureRow",
    "IncidentReport",
    "IncidentAnalysisRequest",
    "NormalizedEvent",
    "NormalizedLog",
    "PromptGuardRequest",
    "RiskResult",
    "URLDetectionRequest",
    "UnifiedIncidentOutput",
]
