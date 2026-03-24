"""Versioned feature matrix schemas for TrustSphere."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FEATURE_SCHEMA_VERSION = "feature.v1"


class FeatureRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[FEATURE_SCHEMA_VERSION] = FEATURE_SCHEMA_VERSION
    entity_id: str
    timestamp: datetime
    features: dict[str, float]


class FeatureMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[FEATURE_SCHEMA_VERSION] = FEATURE_SCHEMA_VERSION
    rows: list[FeatureRow]
    feature_columns: list[str]
