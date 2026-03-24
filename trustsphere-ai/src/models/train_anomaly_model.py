"""Core training pipeline for TrustSphere UEBA anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import ParameterGrid

try:
    import mlflow
except Exception:
    mlflow = None

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

try:
    from .config import (
        ANOMALY_ARTIFACTS_DIR,
        ARTIFACTS_DIR,
        AUTOENCODER_BATCH_SIZE,
        AUTOENCODER_EPOCHS,
        AUTOENCODER_LEARNING_RATE,
        AUTOENCODER_THRESHOLD_QUANTILE,
        CONTAMINATION_RATE,
        DEFAULT_DATASET_PATH,
        FALLBACK_DATASET_PATH,
        MODEL_VERSION,
        MLRUNS_DIR,
        RANDOM_STATE,
        SAVED_MODELS_DIR,
        TIME_AWARE_SPLITS,
    )
    from .evaluate_model import evaluate_model
    from .feature_engineering import BehavioralFeatureEngineer
    from .preprocessing import fit_scaler, transform_data
except ImportError:
    from config import (
        ANOMALY_ARTIFACTS_DIR,
        ARTIFACTS_DIR,
        AUTOENCODER_BATCH_SIZE,
        AUTOENCODER_EPOCHS,
        AUTOENCODER_LEARNING_RATE,
        AUTOENCODER_THRESHOLD_QUANTILE,
        CONTAMINATION_RATE,
        DEFAULT_DATASET_PATH,
        FALLBACK_DATASET_PATH,
        MODEL_VERSION,
        MLRUNS_DIR,
        RANDOM_STATE,
        SAVED_MODELS_DIR,
        TIME_AWARE_SPLITS,
    )
    from evaluate_model import evaluate_model
    from feature_engineering import BehavioralFeatureEngineer
    from preprocessing import fit_scaler, transform_data

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DetectionTrainingArtifacts:
    scores_df: pd.DataFrame
    metrics: dict[str, Any]
    thresholds: dict[str, float]
    selected_features: list[str]


class ShallowAutoencoder:
    """PyTorch autoencoder with safe fallback behavior when torch is unavailable."""

    def __init__(self, input_dim: int) -> None:
        self.input_dim = input_dim
        self.threshold_: float = 0.0
        self.available = TORCH_AVAILABLE
        self.model: Any | None = None
        if self.available:
            self.model = _TorchAutoencoder(input_dim)

    def fit(self, x_train: np.ndarray, x_val: np.ndarray) -> None:
        if not self.available or self.model is None:
            self.threshold_ = float(np.quantile(np.zeros(len(x_train)), AUTOENCODER_THRESHOLD_QUANTILE))
            return
        torch.manual_seed(RANDOM_STATE)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=AUTOENCODER_LEARNING_RATE)
        criterion = nn.MSELoss()
        train_dataset = TensorDataset(torch.tensor(x_train, dtype=torch.float32))
        train_loader = DataLoader(train_dataset, batch_size=min(AUTOENCODER_BATCH_SIZE, len(x_train)), shuffle=True)
        self.model.train()
        for _ in range(AUTOENCODER_EPOCHS):
            for (batch,) in train_loader:
                optimizer.zero_grad()
                reconstructed = self.model(batch)
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()
        train_errors = self.reconstruction_error(x_train)
        self.threshold_ = float(np.quantile(train_errors, AUTOENCODER_THRESHOLD_QUANTILE))

    def reconstruction_error(self, x_values: np.ndarray) -> np.ndarray:
        if not self.available or self.model is None:
            centered = x_values - np.mean(x_values, axis=0, keepdims=True)
            return np.mean(centered**2, axis=1)
        self.model.eval()
        with torch.no_grad():
            tensor = torch.tensor(x_values, dtype=torch.float32)
            reconstructed = self.model(tensor)
            error = torch.mean((reconstructed - tensor) ** 2, dim=1)
        return error.cpu().numpy()

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.available and self.model is not None:
            torch.save({"state_dict": self.model.state_dict(), "threshold": self.threshold_}, output_path)
        else:
            joblib.dump({"threshold": self.threshold_, "available": False}, output_path)


if TORCH_AVAILABLE:
    class _TorchAutoencoder(nn.Module):
        def __init__(self, input_dim: int) -> None:
            super().__init__()
            bottleneck = max(8, input_dim // 4)
            self.encoder = nn.Sequential(nn.Linear(input_dim, max(16, input_dim // 2)), nn.ReLU(), nn.Linear(max(16, input_dim // 2), bottleneck), nn.ReLU())
            self.decoder = nn.Sequential(nn.Linear(bottleneck, max(16, input_dim // 2)), nn.ReLU(), nn.Linear(max(16, input_dim // 2), input_dim))

        def forward(self, x_tensor):
            return self.decoder(self.encoder(x_tensor))


def load_dataset(dataset_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH
    if not path.exists() and Path(FALLBACK_DATASET_PATH).exists():
        path = Path(FALLBACK_DATASET_PATH)
    if not path.exists():
        raise FileNotFoundError(f"No dataset found at {path}")
    if path.suffix == ".json":
        dataframe = pd.read_json(path)
    elif path.suffix == ".parquet":
        dataframe = pd.read_parquet(path)
    else:
        dataframe = pd.read_csv(path)
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
    return dataframe


def run_training(dataset_path: str | Path | None = None) -> DetectionTrainingArtifacts:
    dataframe = load_dataset(dataset_path)
    feature_engineer = BehavioralFeatureEngineer()
    features = feature_engineer.fit_transform(dataframe)
    entity_labels = _derive_labels(dataframe, features.metadata_df["entity_id"].tolist())
    train_idx, val_idx, test_idx = _time_aware_split(features.metadata_df)

    scaler_pipeline, feature_columns = fit_scaler(features.selected_features.iloc[train_idx], SAVED_MODELS_DIR / "scaler.pkl")
    x_train = transform_data(features.selected_features.iloc[train_idx], scaler_pipeline, feature_columns)
    x_val = transform_data(features.selected_features.iloc[val_idx], scaler_pipeline, feature_columns)
    x_test = transform_data(features.selected_features.iloc[test_idx], scaler_pipeline, feature_columns)

    best_iforest, iforest_threshold, iforest_report = _train_isolation_forest(x_train, x_val, entity_labels[val_idx])
    iforest_scores_train = _normalize_scores(-best_iforest.score_samples(x_train))
    iforest_scores_val = _normalize_scores(-best_iforest.score_samples(x_val))
    iforest_scores_test = _normalize_scores(-best_iforest.score_samples(x_test))

    autoencoder = ShallowAutoencoder(input_dim=x_train.shape[1])
    autoencoder.fit(x_train, x_val)
    ae_scores_test = _normalize_scores(autoencoder.reconstruction_error(x_test))

    anomaly_score = np.clip(0.7 * iforest_scores_test + 0.3 * ae_scores_test, 0.0, 1.0)
    anomaly_label = (anomaly_score >= iforest_threshold).astype(int)

    scores_df = features.metadata_df.iloc[test_idx].reset_index(drop=True).copy()
    scores_df["anomaly_score"] = anomaly_score
    scores_df["reconstruction_error"] = ae_scores_test
    scores_df["anomaly_label"] = anomaly_label
    scores_df["behavioral_risk"] = _behavioral_risk_proxy(dataframe, scores_df)
    scores_df["historical_risk"] = _historical_risk_proxy(scores_df)

    thresholds = {
        "anomaly_threshold": float(iforest_threshold),
        "autoencoder_threshold": float(autoencoder.threshold_),
    }
    labels_test = entity_labels[test_idx] if entity_labels is not None else None
    metrics = evaluate_model(
        model_name="IsolationForest+Autoencoder",
        anomaly_scores=anomaly_score,
        labels=labels_test,
        transformed_features=x_test,
        thresholds=thresholds,
        report_path=ARTIFACTS_DIR / "model_report.json",
    )

    _save_artifacts(best_iforest, autoencoder, scaler_pipeline, feature_columns, thresholds, metrics)
    _maybe_log_mlflow(metrics, thresholds, feature_columns)
    return DetectionTrainingArtifacts(scores_df=scores_df, metrics=metrics, thresholds=thresholds, selected_features=feature_columns)


def _train_isolation_forest(x_train: np.ndarray, x_val: np.ndarray, y_val: np.ndarray | None):
    param_grid = ParameterGrid(
        {
            "n_estimators": [100, 200],
            "max_samples": ["auto", 0.8],
            "contamination": [0.01, 0.02, 0.05],
        }
    )
    best_model = None
    best_threshold = 0.95
    best_metric = -np.inf
    best_report = {}
    for params in param_grid:
        model = IsolationForest(random_state=RANDOM_STATE, n_jobs=-1, **params)
        model.fit(x_train)
        val_scores = _normalize_scores(-model.score_samples(x_val))
        threshold = float(np.quantile(val_scores, 1.0 - params["contamination"]))
        predicted = (val_scores >= threshold).astype(int)
        metric = float(val_scores.std())
        if y_val is not None and len(np.unique(y_val)) > 1:
            metric += float(((predicted == 1) & (y_val == 1)).sum()) / max(1, int((y_val == 1).sum()))
        if metric > best_metric:
            best_model = model
            best_threshold = threshold
            best_metric = metric
            best_report = {"params": params, "validation_metric": metric}
    LOGGER.info("Best IsolationForest config: %s", best_report)
    return best_model, best_threshold, best_report


def _save_artifacts(model: IsolationForest, autoencoder: ShallowAutoencoder, scaler_pipeline: Any, feature_columns: list[str], thresholds: dict[str, float], metrics: dict[str, Any]) -> None:
    ANOMALY_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, SAVED_MODELS_DIR / "model_iforest.pkl")
    joblib.dump(model, ANOMALY_ARTIFACTS_DIR / "model_iforest.pkl")
    autoencoder.save(SAVED_MODELS_DIR / "model_autoencoder.pt")
    autoencoder.save(ANOMALY_ARTIFACTS_DIR / "model_autoencoder.pt")
    with (ANOMALY_ARTIFACTS_DIR / "feature_schema.json").open("w", encoding="utf-8") as handle:
        json.dump(feature_columns, handle, indent=2)
    metadata = {
        "training_date": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feature_columns),
        "thresholds": thresholds,
        "metrics": metrics.get("metrics", {}),
        "model_version": MODEL_VERSION,
    }
    _write_yaml(ANOMALY_ARTIFACTS_DIR / "model_metadata.yaml", metadata)


def _write_yaml(output_path: Path, payload: dict[str, Any]) -> None:
    lines = []
    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {json.dumps(child_value)}")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _time_aware_split(metadata_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered = metadata_df.sort_values("timestamp").reset_index()
    n_rows = len(ordered)
    train_end = max(1, int(n_rows * TIME_AWARE_SPLITS[0]))
    val_end = min(n_rows - 1, train_end + max(1, int(n_rows * TIME_AWARE_SPLITS[1])))
    train_idx = ordered.loc[: train_end - 1, "index"].to_numpy()
    val_idx = ordered.loc[train_end: val_end - 1, "index"].to_numpy()
    test_idx = ordered.loc[val_end:, "index"].to_numpy()
    if len(test_idx) == 0:
        test_idx = val_idx
    return train_idx, val_idx, test_idx


def _derive_labels(dataframe: pd.DataFrame, entity_ids: list[str]) -> np.ndarray | None:
    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if "label" not in frame.columns:
        return None
    entity_column = "user_id" if "user_id" in frame.columns else "user" if "user" in frame.columns else "host_id" if "host_id" in frame.columns else "host"
    if entity_column not in frame.columns:
        return None
    frame["entity_id"] = frame[entity_column].astype(str).str.strip().str.lower()
    grouped = frame.groupby("entity_id")["label"].apply(lambda s: int(s.astype(str).str.lower().isin(["attack", "anomaly", "suspicious"]).any()))
    return grouped.reindex(entity_ids).fillna(0).astype(int).to_numpy()


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    if np.allclose(scores.max(), scores.min()):
        return np.zeros_like(scores)
    return (scores - scores.min()) / (scores.max() - scores.min())


def _behavioral_risk_proxy(dataframe: pd.DataFrame, scores_df: pd.DataFrame) -> np.ndarray:
    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    entity_column = "user_id" if "user_id" in frame.columns else "user" if "user" in frame.columns else "host_id" if "host_id" in frame.columns else "host"
    frame["entity_id"] = frame[entity_column].astype(str).str.strip().str.lower()
    frame["status"] = (frame["status"] if "status" in frame.columns else pd.Series(["unknown"] * len(frame), index=frame.index)).astype(str).str.lower()
    event_series = (frame["event_type"] if "event_type" in frame.columns else pd.Series(["unknown"] * len(frame), index=frame.index)).astype(str).str.lower()
    frame["failed_ratio"] = frame["status"].isin(["fail", "failed", "error", "denied"]).astype(float)
    frame["privilege_flag"] = event_series.str.contains("privilege|admin_action", regex=True).astype(float)
    grouped = frame.groupby("entity_id").agg(failed_ratio=("failed_ratio", "mean"), privilege_flag=("privilege_flag", "mean"))
    values = grouped.reindex(scores_df["entity_id"]).fillna(0.0)
    return np.clip(0.7 * values["failed_ratio"].to_numpy() + 0.3 * values["privilege_flag"].to_numpy(), 0.0, 1.0)


def _historical_risk_proxy(scores_df: pd.DataFrame) -> np.ndarray:
    ranked = scores_df.sort_values(["entity_id", "timestamp"]).copy()
    rolling = ranked.groupby("entity_id").cumcount().to_numpy(dtype=float)
    if len(rolling) == 0 or np.allclose(rolling.max(), rolling.min()):
        return np.zeros(len(scores_df), dtype=float)
    normalized = (rolling - rolling.min()) / (rolling.max() - rolling.min())
    ranked["historical_risk"] = normalized
    return ranked.sort_index()["historical_risk"].to_numpy(dtype=float)


def _maybe_log_mlflow(metrics: dict[str, Any], thresholds: dict[str, float], feature_columns: list[str]) -> None:
    if mlflow is None:
        LOGGER.info("MLflow not installed; skipping experiment tracking.")
        return
    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
    with mlflow.start_run(run_name=MODEL_VERSION):
        mlflow.log_params({"feature_count": len(feature_columns), **thresholds})
        for key, value in metrics.get("metrics", {}).items():
            if isinstance(value, (int, float)) and value is not None:
                mlflow.log_metric(key, value)


if __name__ == "__main__":
    artifacts = run_training()
    print(json.dumps({"rows": len(artifacts.scores_df), "thresholds": artifacts.thresholds, "metrics": artifacts.metrics.get("metrics", {})}, indent=2))
