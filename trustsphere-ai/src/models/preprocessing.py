"""Preprocessing pipeline for TrustSphere UEBA training."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

try:
    from .config import PCA_ENABLED, PCA_VARIANCE
except ImportError:
    from config import PCA_ENABLED, PCA_VARIANCE


LOGGER = logging.getLogger(__name__)


def build_preprocessing_pipeline(enable_pca: bool = PCA_ENABLED) -> Pipeline:
    """Create the reusable numeric preprocessing pipeline."""
    steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", RobustScaler()),
        ("variance", VarianceThreshold(0.01)),
    ]
    if enable_pca:
        steps.append(("pca", PCA(n_components=PCA_VARIANCE, svd_solver="full", random_state=42)))
    return Pipeline(steps)


def fit_preprocessing_pipeline(
    features_df: pd.DataFrame,
    output_path: str | Path | None = None,
    enable_pca: bool = PCA_ENABLED,
) -> tuple[Pipeline, list[str]]:
    """Fit preprocessing on numeric features and optionally persist it."""
    numeric_columns = features_df.select_dtypes(include=["number", "bool"]).columns.tolist()
    if not numeric_columns:
        raise ValueError("No numeric columns available for preprocessing.")

    pipeline = build_preprocessing_pipeline(enable_pca=enable_pca)
    pipeline.fit(features_df[numeric_columns])

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": pipeline, "feature_columns": numeric_columns}, output_path)
        LOGGER.info("Saved preprocessing pipeline to %s", output_path)

    return pipeline, numeric_columns


def transform_features(features_df: pd.DataFrame, pipeline: Pipeline, feature_columns: list[str]):
    """Transform features using the fitted preprocessing pipeline."""
    return pipeline.transform(features_df[feature_columns])
