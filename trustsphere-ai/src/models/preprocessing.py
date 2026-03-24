"""Preprocessing utilities for the TrustSphere detection pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from .config import SCALER_ARTIFACTS_DIR
except ImportError:
    from config import SCALER_ARTIFACTS_DIR


LOGGER = logging.getLogger(__name__)


def build_scaler_pipeline() -> Pipeline:
    """Create the production preprocessing pipeline."""
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("variance", VarianceThreshold(0.0)),
        ]
    )


def fit_scaler(features_df: pd.DataFrame, output_path: str | Path | None = None) -> tuple[Pipeline, list[str]]:
    """Fit the scaler on numeric columns and optionally persist it."""
    numeric_columns = features_df.select_dtypes(include=["number", "bool"]).columns.tolist()
    if not numeric_columns:
        raise ValueError("No numeric feature columns available for scaling.")
    pipeline = build_scaler_pipeline()
    pipeline.fit(features_df[numeric_columns])
    destination = Path(output_path) if output_path else SCALER_ARTIFACTS_DIR / "scaler.pkl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "feature_columns": numeric_columns}, destination)
    LOGGER.info("Saved scaler pipeline to %s", destination)
    return pipeline, numeric_columns


def transform_data(features_df: pd.DataFrame, pipeline: Pipeline, feature_columns: list[str]):
    """Apply the fitted preprocessing pipeline to a dataframe."""
    prepared = features_df.copy()
    for column in feature_columns:
        if column not in prepared.columns:
            prepared[column] = 0.0
    return pipeline.transform(prepared[feature_columns])
