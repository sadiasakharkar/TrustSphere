"""Production inference pipeline for TrustSphere UEBA anomaly detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

try:
    from .config import SAVED_MODELS_DIR
    from .feature_engineering import BehavioralFeatureEngineer
    from .preprocessing import transform_features
except ImportError:
    from config import SAVED_MODELS_DIR
    from feature_engineering import BehavioralFeatureEngineer
    from preprocessing import transform_features


LOGGER = logging.getLogger(__name__)


class UEBAInferencePipeline:
    """Offline inference pipeline using saved feature engineering and model artifacts."""

    def __init__(self, model_dir: str | Path = SAVED_MODELS_DIR) -> None:
        self.model_dir = Path(model_dir)
        self.model = joblib.load(self.model_dir / "anomaly_model.pkl")
        preprocessing_bundle = joblib.load(self.model_dir / "preprocessing_pipeline.pkl")
        if isinstance(preprocessing_bundle, dict):
            self.preprocessing_pipeline = preprocessing_bundle["pipeline"]
            self.feature_columns = preprocessing_bundle["feature_columns"]
        else:
            self.preprocessing_pipeline = preprocessing_bundle
            with (self.model_dir / "feature_columns.json").open("r", encoding="utf-8") as handle:
                self.feature_columns = json.load(handle)
        self.feature_engineer = BehavioralFeatureEngineer()

    def predict(self, log_dataframe: pd.DataFrame) -> pd.DataFrame:
        """Predict anomaly scores for a batch of normalized logs."""
        engineered = self.feature_engineer.transform(log_dataframe)
        transformed = transform_features(
            engineered.features_df,
            self.preprocessing_pipeline,
            self.feature_columns,
        )
        scores = np.asarray(self.model.decision_function(transformed), dtype=float)
        threshold = float(np.quantile(scores, 0.95))
        labels = (scores >= threshold).astype(int)

        result = engineered.metadata_df.copy()
        result["anomaly_score"] = scores
        result["anomaly_label"] = labels
        return result

    def predict_single_event(self, event_dict: dict[str, Any]) -> dict[str, Any]:
        """Predict anomaly for a single normalized event."""
        frame = pd.DataFrame([event_dict])
        result = self.predict(frame)
        row = result.iloc[0]
        return {
            "anomaly_score": float(row["anomaly_score"]),
            "anomaly_label": int(row["anomaly_label"]),
        }
