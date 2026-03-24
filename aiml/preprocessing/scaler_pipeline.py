"""Scaling utilities for the offline TrustSphere pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler


LOGGER = logging.getLogger(__name__)


def fit_scaler(
    df: pd.DataFrame,
    scaler_type: str = "standard",
    artifact_path: str | Path | None = None,
) -> tuple[Any, list[str]]:
    """Fit a scaler on all numeric columns and optionally persist it."""
    numeric_columns = df.select_dtypes(include=["number", "bool"]).columns.tolist()
    if not numeric_columns:
        raise ValueError("No numeric columns available for scaling.")

    scaler = StandardScaler() if scaler_type.lower() == "standard" else RobustScaler()
    scaler.fit(df[numeric_columns])

    if artifact_path is not None:
        artifact_path = Path(artifact_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"scaler": scaler, "columns": numeric_columns, "scaler_type": scaler_type}, artifact_path)
        LOGGER.info("Scaler saved to %s", artifact_path)

    return scaler, numeric_columns


def transform_data(df: pd.DataFrame, scaler: Any, columns: list[str]) -> pd.DataFrame:
    """Apply a fitted scaler to a dataframe copy."""
    transformed = df.copy()
    transformed[columns] = scaler.transform(transformed[columns])
    return transformed
