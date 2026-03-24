"""Training runner for the TrustSphere UEBA anomaly model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from pyod.models.iforest import IForest

try:
    from .config import (
        ARTIFACTS_DIR,
        CONTAMINATION_RATE,
        DEFAULT_DATASET_PATH,
        MIN_REQUIRED_COLUMNS,
        MODEL_VERSION,
        RANDOM_STATE,
        SAVED_MODELS_DIR,
    )
    from .evaluate_model import evaluate_model
    from .feature_engineering import BehavioralFeatureEngineer
    from .preprocessing import fit_preprocessing_pipeline, transform_features
except ImportError:
    from config import (
        ARTIFACTS_DIR,
        CONTAMINATION_RATE,
        DEFAULT_DATASET_PATH,
        MIN_REQUIRED_COLUMNS,
        MODEL_VERSION,
        RANDOM_STATE,
        SAVED_MODELS_DIR,
    )
    from evaluate_model import evaluate_model
    from feature_engineering import BehavioralFeatureEngineer
    from preprocessing import fit_preprocessing_pipeline, transform_features


LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@dataclass(slots=True)
class TrainingArtifacts:
    """Model artifacts produced by the training pipeline."""

    model: Any
    preprocessing_pipeline: Any
    feature_columns: list[str]
    metadata: dict[str, Any]
    report: dict[str, Any]


def load_dataset(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load normalized CERT log data."""
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    frame = pd.read_csv(dataset_path)
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    missing_columns = [column for column in MIN_REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")
    return frame


def train_best_model(
    transformed_features: np.ndarray,
    contamination_rate: float = CONTAMINATION_RATE,
) -> tuple[IForest, dict[str, Any], np.ndarray]:
    """Train Isolation Forest across a small hyperparameter grid and select best separation."""
    candidate_params = [
        {"n_estimators": 100, "max_samples": "auto", "contamination": 0.01},
        {"n_estimators": 100, "max_samples": "auto", "contamination": 0.02},
        {"n_estimators": 100, "max_samples": "auto", "contamination": 0.05},
        {"n_estimators": 100, "max_samples": 0.8, "contamination": 0.01},
        {"n_estimators": 100, "max_samples": 0.8, "contamination": 0.02},
        {"n_estimators": 100, "max_samples": 0.8, "contamination": 0.05},
        {"n_estimators": 200, "max_samples": "auto", "contamination": 0.01},
        {"n_estimators": 200, "max_samples": "auto", "contamination": 0.02},
        {"n_estimators": 200, "max_samples": "auto", "contamination": 0.05},
        {"n_estimators": 200, "max_samples": 0.8, "contamination": 0.01},
        {"n_estimators": 200, "max_samples": 0.8, "contamination": 0.02},
        {"n_estimators": 200, "max_samples": 0.8, "contamination": 0.05},
    ]

    best_model: IForest | None = None
    best_params: dict[str, Any] | None = None
    best_scores: np.ndarray | None = None
    best_metric = -np.inf

    for params in candidate_params:
        model = IForest(
            random_state=RANDOM_STATE,
            behaviour="new",
            **params,
        )
        model.fit(transformed_features)
        scores = np.asarray(model.decision_function(transformed_features), dtype=float)
        metric = _anomaly_separation_metric(scores)
        LOGGER.info("Model params=%s separation_metric=%.6f", params, metric)
        if metric > best_metric:
            best_metric = metric
            best_model = model
            best_params = params
            best_scores = scores

    if best_model is None or best_params is None or best_scores is None:
        raise RuntimeError("Model search failed to produce a valid Isolation Forest.")
    return best_model, best_params, best_scores


def save_training_artifacts(
    model: IForest,
    preprocessing_pipeline: Any,
    feature_columns: list[str],
    metadata: dict[str, Any],
) -> None:
    """Persist model, preprocessing, and metadata artifacts."""
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, SAVED_MODELS_DIR / "anomaly_model.pkl")
    joblib.dump(preprocessing_pipeline, SAVED_MODELS_DIR / "preprocessing_pipeline.pkl")
    with (SAVED_MODELS_DIR / "feature_columns.json").open("w", encoding="utf-8") as handle:
        json.dump(feature_columns, handle, indent=2)
    with (SAVED_MODELS_DIR / "model_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)


def run_training(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> TrainingArtifacts:
    """Run the complete feature-engineering, training, evaluation, and export flow."""
    dataframe = load_dataset(dataset_path)
    feature_engineer = BehavioralFeatureEngineer()
    engineering_result = feature_engineer.fit_transform(dataframe)
    preprocessing_pipeline, feature_columns = fit_preprocessing_pipeline(
        engineering_result.features_df,
        output_path=SAVED_MODELS_DIR / "preprocessing_pipeline.pkl",
    )
    transformed_features = transform_features(
        engineering_result.features_df,
        preprocessing_pipeline,
        feature_columns,
    )

    contamination = _estimate_contamination(engineering_result.features_df)
    model, best_params, scores = train_best_model(transformed_features, contamination_rate=contamination)
    labels = _derive_optional_labels(dataframe)
    report = evaluate_model(
        model_name="IsolationForest",
        scores=scores,
        labels=labels,
        transformed_features=transformed_features,
        feature_columns=feature_columns,
        training_rows=len(engineering_result.features_df),
        anomaly_ratio=float((scores >= np.quantile(scores, 0.95)).mean()),
        report_path=ARTIFACTS_DIR / "model_report.json",
    )

    metadata = {
        "training_date": datetime.utcnow().isoformat(),
        "dataset_name": str(Path(dataset_path).name),
        "contamination": float(best_params["contamination"]),
        "feature_list": feature_columns,
        "version": MODEL_VERSION,
        "best_params": best_params,
    }
    save_training_artifacts(model, preprocessing_pipeline, feature_columns, metadata)

    LOGGER.info(
        "Training complete | rows=%s | features=%s | contamination=%.4f",
        len(engineering_result.features_df),
        len(feature_columns),
        float(best_params["contamination"]),
    )
    return TrainingArtifacts(
        model=model,
        preprocessing_pipeline=preprocessing_pipeline,
        feature_columns=feature_columns,
        metadata=metadata,
        report=report,
    )


def _estimate_contamination(features_df: pd.DataFrame) -> float:
    heuristic = (
        (features_df.get("failed_login_ratio", 0) > 0.3)
        | (features_df.get("night_activity_ratio", 0) > 0.25)
        | (features_df.get("new_device_flag", 0) > 0)
    )
    contamination = float(np.clip(np.mean(heuristic), 0.01, 0.05))
    return contamination


def _derive_optional_labels(dataframe: pd.DataFrame) -> np.ndarray | None:
    if "label" not in dataframe.columns:
        return None
    labels = dataframe["label"].astype(str).str.lower()
    return labels.isin(["attack", "suspicious", "anomaly"]).astype(int).to_numpy()


def _anomaly_separation_metric(scores: np.ndarray) -> float:
    upper_tail = float(np.percentile(scores, 95))
    median = float(np.median(scores))
    std_dev = float(np.std(scores) + 1e-6)
    return (upper_tail - median) / std_dev


if __name__ == "__main__":
    artifacts = run_training()
    print(
        json.dumps(
            {
                "model_version": MODEL_VERSION,
                "feature_count": len(artifacts.feature_columns),
                "dataset_name": artifacts.metadata["dataset_name"],
                "contamination": artifacts.metadata["contamination"],
            },
            indent=2,
        )
    )
