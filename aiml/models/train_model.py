"""Offline anomaly model training and selection for TrustSphere."""

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
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM


LOGGER = logging.getLogger(__name__)
RANDOM_SEED = 42


@dataclass(slots=True)
class TrainingResult:
    """Encapsulates trained model outputs and metadata."""

    selected_model_name: str
    selected_model: Any
    isolation_forest_model: IsolationForest
    feature_columns: list[str]
    scored_frame: pd.DataFrame
    metrics: dict[str, dict[str, float]]
    metadata: dict[str, Any]


def train_and_select_model(
    features_df: pd.DataFrame,
    feature_columns: list[str],
    artifact_dir: str | Path,
) -> TrainingResult:
    """Train Isolation Forest, One-Class SVM, and LOF, then select the strongest model."""
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    train_matrix = features_df[feature_columns].to_numpy(dtype=float)
    contamination = _estimate_contamination(features_df)

    models: dict[str, Any] = {
        "IsolationForest": IsolationForest(
            n_estimators=300,
            contamination=contamination,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "OneClassSVM": OneClassSVM(kernel="rbf", gamma="scale", nu=max(contamination, 0.02)),
        "LocalOutlierFactor": LocalOutlierFactor(
            novelty=True,
            contamination=contamination,
            n_neighbors=max(10, min(35, len(features_df) - 1)),
        ),
    }

    metrics: dict[str, dict[str, float]] = {}
    predictions: dict[str, np.ndarray] = {}
    score_vectors: dict[str, np.ndarray] = {}

    for model_name, model in models.items():
        LOGGER.info("Training model: %s", model_name)
        model.fit(train_matrix)
        scores = _compute_scores(model_name, model, train_matrix)
        threshold = float(np.quantile(scores, 1.0 - contamination))
        predictions[model_name] = (scores >= threshold).astype(int)
        score_vectors[model_name] = scores
        metrics[model_name] = {
            "anomaly_score_variance": float(np.var(scores)),
            "stability_metric": _stability_metric(model_name, model, train_matrix),
            "silhouette_like_separation": _silhouette_like_separation(scores, predictions[model_name]),
        }

    selected_model_name = max(
        metrics,
        key=lambda name: (
            metrics[name]["stability_metric"]
            + metrics[name]["silhouette_like_separation"]
            + np.log1p(metrics[name]["anomaly_score_variance"])
        ),
    )
    selected_model = models[selected_model_name]
    isolation_forest_model = models["IsolationForest"]

    final_scores = score_vectors[selected_model_name]
    final_predictions = predictions[selected_model_name]
    scored_frame = features_df.copy()
    scored_frame["anomaly_score"] = final_scores
    scored_frame["is_anomaly"] = final_predictions

    joblib.dump(isolation_forest_model, artifact_dir / "isolation_forest.pkl")
    joblib.dump(selected_model, artifact_dir / "final_model.pkl")
    scored_frame.to_csv(artifact_dir / "scored_features.csv", index=False)

    metadata = {
        "training_timestamp": datetime.utcnow().isoformat(),
        "dataset_size": int(len(features_df)),
        "selected_model_name": selected_model_name,
        "feature_count": int(len(feature_columns)),
        "contamination": float(contamination),
    }
    LOGGER.info("Selected model: %s", selected_model_name)

    return TrainingResult(
        selected_model_name=selected_model_name,
        selected_model=selected_model,
        isolation_forest_model=isolation_forest_model,
        feature_columns=feature_columns,
        scored_frame=scored_frame,
        metrics=metrics,
        metadata=metadata,
    )


def _estimate_contamination(features_df: pd.DataFrame) -> float:
    heuristic = (
        (features_df.get("failed_login_ratio", 0) > 0.25)
        | (features_df.get("night_activity_ratio", 0) > 0.20)
        | (features_df.get("unique_ip_count", 0) > features_df.get("unique_ip_count", pd.Series([0])).quantile(0.95))
    )
    contamination = float(np.clip(np.mean(heuristic), 0.01, 0.08))
    return contamination


def _compute_scores(model_name: str, model: Any, train_matrix: np.ndarray) -> np.ndarray:
    if model_name == "LocalOutlierFactor":
        raw_scores = -model.score_samples(train_matrix)
    else:
        raw_scores = -model.score_samples(train_matrix)
    return np.asarray(raw_scores, dtype=float)


def _stability_metric(model_name: str, model: Any, train_matrix: np.ndarray) -> float:
    """Measure consistency of anomaly scores across bootstrap samples."""
    if len(train_matrix) < 20:
        return 0.5
    rng = np.random.default_rng(RANDOM_SEED)
    reference_scores = _compute_scores(model_name, model, train_matrix[: min(len(train_matrix), 2000)])
    correlations: list[float] = []

    for _ in range(3):
        sample_indices = rng.choice(len(train_matrix), size=max(int(len(train_matrix) * 0.8), 10), replace=True)
        sample = train_matrix[sample_indices]
        sampled_model = _clone_model(model_name, model)
        sampled_model.fit(sample)
        rescored = _compute_scores(model_name, sampled_model, train_matrix[: min(len(train_matrix), 2000)])
        correlation = np.corrcoef(reference_scores, rescored)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0
        correlations.append(float(correlation))

    return float(np.clip(np.mean(correlations), 0.0, 1.0))


def _silhouette_like_separation(scores: np.ndarray, labels: np.ndarray) -> float:
    normal_scores = scores[labels == 0]
    anomaly_scores = scores[labels == 1]
    if len(normal_scores) == 0 or len(anomaly_scores) == 0:
        return 0.0
    numerator = float(abs(np.mean(anomaly_scores) - np.mean(normal_scores)))
    denominator = float(np.std(scores) + 1e-6)
    return float(numerator / denominator)


def _clone_model(model_name: str, model: Any) -> Any:
    if model_name == "IsolationForest":
        return IsolationForest(
            n_estimators=model.n_estimators,
            contamination=model.contamination,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    if model_name == "OneClassSVM":
        return OneClassSVM(kernel=model.kernel, gamma=model.gamma, nu=model.nu)
    if model_name == "LocalOutlierFactor":
        return LocalOutlierFactor(
            novelty=True,
            contamination=model.contamination,
            n_neighbors=model.n_neighbors,
        )
    raise ValueError(f"Unsupported model: {model_name}")
