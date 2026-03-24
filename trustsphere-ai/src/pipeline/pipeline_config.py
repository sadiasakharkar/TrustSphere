"""Configuration for unified TrustSphere pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class UnifiedPipelineConfig:
    production_mode: bool = False
    allow_fallbacks: bool = True
    require_schema_version_match: bool = True
    require_model_artifacts: bool = True
    require_ollama_available: bool = False

    @classmethod
    def from_env(cls) -> "UnifiedPipelineConfig":
        env = os.getenv("TRUSTSPHERE_ENV", "development").strip().lower()
        production = env in {"prod", "production"}
        return cls(
            production_mode=production,
            allow_fallbacks=not production,
            require_schema_version_match=True,
            require_model_artifacts=True,
            require_ollama_available=production,
        )
