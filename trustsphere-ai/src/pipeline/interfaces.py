"""Protocol interfaces for unified TrustSphere orchestration."""

from __future__ import annotations

from typing import Protocol

from ..contracts import (
    AnomalyResult,
    AttackGraphResult,
    DetectorFindingBatch,
    FeatureMatrix,
    IncidentReport,
    NormalizedEvent,
    RiskResult,
)


class EventNormalizerInterface(Protocol):
    def normalize(self, raw_input: object) -> list[NormalizedEvent]: ...


class FeatureProducerInterface(Protocol):
    def produce(self, events: list[NormalizedEvent]) -> FeatureMatrix: ...


class DetectorAdapterInterface(Protocol):
    def detect(self, events: list[NormalizedEvent]) -> DetectorFindingBatch: ...


class AnomalyEngineInterface(Protocol):
    def score(self, events: list[NormalizedEvent], feature_matrix: FeatureMatrix) -> list[AnomalyResult]: ...


class RiskEngineInterface(Protocol):
    def evaluate(
        self,
        events: list[NormalizedEvent],
        anomalies: list[AnomalyResult],
        findings: DetectorFindingBatch,
    ) -> list[RiskResult]: ...


class GraphEngineInterface(Protocol):
    def build(self, events: list[NormalizedEvent], risks: list[RiskResult]) -> AttackGraphResult: ...


class SocReasonerInterface(Protocol):
    def analyze(
        self,
        events: list[NormalizedEvent],
        findings: DetectorFindingBatch,
        risks: list[RiskResult],
        graph: AttackGraphResult,
    ) -> IncidentReport: ...
