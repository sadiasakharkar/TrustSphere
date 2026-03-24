"""Compatibility wrapper around the unified TrustSphere intelligence pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts import IncidentReport, NormalizedEvent, NormalizedLog
from .pipeline_config import UnifiedPipelineConfig
from .unified_intelligence_pipeline import UnifiedIntelligencePipeline


class TrustSpherePipeline:
    """Legacy entrypoint preserved for serving-layer compatibility.

    This wrapper delegates orchestration to UnifiedIntelligencePipeline and returns
    the IncidentReport portion expected by existing API consumers.
    """

    def __init__(self, base_dir: str | Path | None = None, config: UnifiedPipelineConfig | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else None
        self.pipeline = UnifiedIntelligencePipeline(base_dir=base_dir, config=config)

    def analyze_incident(self, logs: list[NormalizedEvent] | list[NormalizedLog] | list[dict[str, Any]] | dict[str, Any] | None = None) -> IncidentReport:
        return self.pipeline.run(logs).incident_report
