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
    from .preprocessing import transform_data
except ImportError:
    from config import SAVED_MODELS_DIR
    from feature_engineering import BehavioralFeatureEngineer
    from preprocessing import transform_data


LOGGER = logging.getLogger(__name__)


class UEBAInferencePipeline:
    """Offline inference pipeline using saved feature engineering and model artifacts."""

    def __init__(self, model_dir: str | Path = SAVED_MODELS_DIR) -> None:
        self.model_dir = Path(model_dir)
        model_path = self.model_dir / "model_iforest.pkl"
        if not model_path.exists():
            model_path = self.model_dir / "anomaly_model.pkl"
        self.model = joblib.load(model_path)
        preprocessing_path = self.model_dir / "scaler.pkl"
        if not preprocessing_path.exists():
            preprocessing_path = self.model_dir / "preprocessing_pipeline.pkl"
        preprocessing_bundle = joblib.load(preprocessing_path)
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
        transformed = transform_data(
            engineered.selected_features,
            self.preprocessing_pipeline,
            self.feature_columns,
        )
        if hasattr(self.model, "score_samples"):
            raw_scores = -np.asarray(self.model.score_samples(transformed), dtype=float)
        else:
            raw_scores = np.asarray(self.model.decision_function(transformed), dtype=float)
        scores = _normalize_scores(raw_scores)
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


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    if np.allclose(scores.max(), scores.min()):
        return np.zeros_like(scores)
    return (scores - scores.min()) / (scores.max() - scores.min())
