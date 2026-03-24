"""Unified pipeline interfaces for TrustSphere intelligence.

Imports are intentionally lazy here so lightweight modules like the normalizer can
be imported without pulling in the full ML/runtime stack.
"""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "TrustSpherePipeline",
    "UnifiedIntelligencePipeline",
]


def __getattr__(name: str):
    if name == "TrustSpherePipeline":
        return import_module("src.pipeline.trustsphere_pipeline").TrustSpherePipeline
    if name == "UnifiedIntelligencePipeline":
        return import_module("src.pipeline.unified_intelligence_pipeline").UnifiedIntelligencePipeline
    raise AttributeError(name)
