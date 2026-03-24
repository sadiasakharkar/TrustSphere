"""Production-grade UEBA anomaly training pipeline for TrustSphere.

This module is designed as SOC-quality ML tooling rather than notebook-only code.
It assumes the CERT Insider Threat `logon.csv` is the initial training source and
builds user/day behavioral aggregates suitable for unsupervised anomaly detection.

Key design choices:
- Time-aware splitting to reduce leakage between train/validation/test windows.
- Robust preprocessing with vectorized pandas operations for 100k+ row workloads.
- Synthetic anomaly injection for validation and model selection when real labels
  are sparse or absent.
- Multi-model training and selection rather than assuming a single algorithm wins.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from pyod.models.hbos import HBOS
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score, silhouette_score
from sklearn.model_selection import ParameterGrid, TimeSeriesSplit
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
from sklearn.svm import OneClassSVM


LOGGER = logging.getLogger("trustsphere.cert_ueba_training")
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


RANDOM_SEED = 42
DEFAULT_CONTAMINATION = 0.03
TRAIN_RATIO = 0.7
VALIDATION_RATIO = 0.15
SYNTHETIC_ANOMALY_RATE = 0.12
AFTER_HOURS_START = 19
AFTER_HOURS_END = 7


@dataclass(slots=True)
class TrainingArtifacts:
    """Saved outputs required for reproducible production inference."""

    model_name: str
    model_path: Path
    scaler_path: Path
    feature_columns_path: Path
    comparison: pd.DataFrame
    feature_columns: list[str]
    best_params: dict[str, Any]


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load raw CERT logs from CSV with predictable schema handling."""
    path = Path(data_path)
    LOGGER.info("Loading CERT data from %s", path)
    dataframe = pd.read_csv(path, low_memory=False)
    if dataframe.empty:
        raise ValueError(f"No records found in {path}")
    LOGGER.info("Loaded %s rows and %s columns", len(dataframe), len(dataframe.columns))
    return dataframe


def normalize_logs(logs: pd.DataFrame) -> pd.DataFrame:
    """Normalize heterogeneous CERT log columns into a canonical event schema."""
    dataframe = logs.copy()
    dataframe.columns = [str(column).strip().lower().replace(" ", "_") for column in dataframe.columns]

    timestamp_col = _resolve_column(dataframe, ["date", "timestamp", "time", "datetime"])
    user_col = _resolve_column(dataframe, ["user", "username"])
    device_col = _resolve_column(dataframe, ["pc", "host", "device", "computer"], required=False)
    activity_col = _resolve_column(dataframe, ["activity", "event_type", "event"], required=False)
    role_col = _resolve_column(dataframe, ["role"], required=False)
    department_col = _resolve_column(dataframe, ["department"], required=False)

    normalized = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(dataframe[timestamp_col], errors="coerce"),
            "user": dataframe[user_col].astype(str).str.strip().str.lower(),
            "device": _series_or_default(dataframe, device_col, "unknown_device"),
            "event_type": _normalize_activity(_series_or_default(dataframe, activity_col, "logon")),
            "role": _series_or_default(dataframe, role_col, "unknown"),
            "department": _series_or_default(dataframe, department_col, "unknown"),
        }
    )

    normalized = normalized.dropna(subset=["timestamp", "user"])
    normalized = normalized[normalized["user"] != ""]
    normalized["event_category"] = normalized["event_type"].map(_derive_event_category)
    normalized["event_source"] = normalized["event_type"].map(_derive_event_source)
    normalized["hour"] = normalized["timestamp"].dt.hour.astype(np.int16)
    normalized["is_weekend"] = (normalized["timestamp"].dt.dayofweek >= 5).astype(np.int8)
    normalized["is_after_hours"] = (
        (normalized["hour"] < AFTER_HOURS_END) | (normalized["hour"] >= AFTER_HOURS_START)
    ).astype(np.int8)
    normalized["is_login"] = normalized["event_type"].isin(["login_success", "login_failed"]).astype(np.int8)
    normalized["is_logout"] = (normalized["event_type"] == "logout").astype(np.int8)
    normalized["event_day"] = normalized["timestamp"].dt.floor("D")
    normalized = normalized.sort_values(["user", "timestamp"]).reset_index(drop=True)
    LOGGER.info("Normalized %s records", len(normalized))
    return normalized


def build_features(events: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Construct UEBA-oriented numeric features at user/day granularity."""
    dataframe = events.copy()
    dataframe["previous_device"] = dataframe.groupby(["user", "event_day"])["device"].shift()
    dataframe["device_switch"] = (
        dataframe["previous_device"].notna() & (dataframe["previous_device"] != dataframe["device"])
    ).astype(np.int8)

    event_counts = (
        dataframe.groupby(["user", "event_day", "event_type"], observed=True)
        .size()
        .rename("event_count")
        .reset_index()
    )
    activity_entropy = (
        event_counts.assign(
            total=lambda frame: frame.groupby(["user", "event_day"])["event_count"].transform("sum"),
            probability=lambda frame: frame["event_count"] / frame["total"],
        )
        .assign(entropy_component=lambda frame: -(frame["probability"] * np.log2(frame["probability"])))
        .groupby(["user", "event_day"], observed=True)["entropy_component"]
        .sum()
        .rename("activity_entropy")
    )

    login_events = dataframe[dataframe["is_login"] == 1].copy()
    login_events["previous_login"] = login_events.groupby(["user", "event_day"])["timestamp"].shift()
    login_events["minutes_between_logins"] = (
        (login_events["timestamp"] - login_events["previous_login"]).dt.total_seconds() / 60.0
    )
    login_stats = (
        login_events.groupby(["user", "event_day"], observed=True)
        .agg(
            first_login_hour=("hour", "min"),
            login_frequency_per_day=("timestamp", "size"),
            mean_time_between_logins=("minutes_between_logins", "mean"),
            login_time_variance=("hour", "var"),
        )
        .fillna({"mean_time_between_logins": 0.0, "login_time_variance": 0.0})
    )

    grouped = dataframe.groupby(["user", "event_day"], observed=True)
    feature_frame = grouped.agg(
        role=("role", "last"),
        department=("department", "last"),
        total_events=("timestamp", "size"),
        after_hours_activity_ratio=("is_after_hours", "mean"),
        weekend_activity_ratio=("is_weekend", "mean"),
        session_duration_estimate=("timestamp", lambda series: (series.max() - series.min()).total_seconds() / 3600.0),
        unique_devices_used=("device", "nunique"),
        unique_activity_types=("event_type", "nunique"),
        device_switch_count=("device_switch", "sum"),
        host_change_frequency=("device", lambda series: series.nunique() / max(len(series), 1)),
    )

    feature_frame = feature_frame.join(activity_entropy, how="left")
    feature_frame = feature_frame.join(login_stats, how="left")
    feature_frame = feature_frame.reset_index()

    feature_frame["device_switch_rate"] = feature_frame["device_switch_count"] / np.maximum(
        feature_frame["total_events"] - 1, 1
    )
    feature_frame["mean_time_between_logins"] = feature_frame["mean_time_between_logins"].fillna(0.0)
    feature_frame["login_time_variance"] = feature_frame["login_time_variance"].fillna(0.0)
    feature_frame["login_frequency_per_day"] = feature_frame["login_frequency_per_day"].fillna(0.0)
    feature_frame["activity_entropy"] = feature_frame["activity_entropy"].fillna(0.0)
    feature_frame["first_login_hour"] = feature_frame["first_login_hour"].fillna(12.0)

    baseline_login_hour = feature_frame.groupby("user", observed=True)["first_login_hour"].transform("median")
    login_hour_mad = feature_frame.groupby("user", observed=True)["first_login_hour"].transform(
        lambda series: np.median(np.abs(series - np.median(series))) + 1e-3
    )
    feature_frame["abnormal_login_hour_score"] = np.abs(
        feature_frame["first_login_hour"] - baseline_login_hour
    ) / login_hour_mad

    feature_frame["session_duration_estimate"] = feature_frame["session_duration_estimate"].clip(lower=0.0, upper=24.0)
    feature_frame["login_frequency_per_day"] = feature_frame["login_frequency_per_day"].clip(lower=0.0)
    feature_frame["unique_devices_used"] = feature_frame["unique_devices_used"].clip(lower=0)
    feature_frame["unique_activity_types"] = feature_frame["unique_activity_types"].clip(lower=0)

    feature_columns = [
        "login_frequency_per_day",
        "after_hours_activity_ratio",
        "weekend_activity_ratio",
        "session_duration_estimate",
        "unique_devices_used",
        "unique_activity_types",
        "device_switch_rate",
        "mean_time_between_logins",
        "login_time_variance",
        "activity_entropy",
        "abnormal_login_hour_score",
        "host_change_frequency",
    ]
    LOGGER.info("Built %s daily user-behavior rows with %s features", len(feature_frame), len(feature_columns))
    return feature_frame, feature_columns


def split_dataset(
    features: pd.DataFrame,
    feature_columns: list[str],
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Create time-aware train/validation/test splits and synthetic-labeled eval sets.

    Assumption:
    The original CERT data is predominantly normal. We therefore train on earlier
    time windows and inject controlled synthetic anomalies into validation/test
    windows for model selection.
    """

    dataframe = features.sort_values(["event_day", "user"]).reset_index(drop=True)
    unique_days = dataframe["event_day"].drop_duplicates().to_list()
    if len(unique_days) < 3:
        raise ValueError("At least 3 unique days are required for time-aware splitting.")

    train_end_index = max(1, int(len(unique_days) * TRAIN_RATIO))
    validation_end_index = max(train_end_index + 1, int(len(unique_days) * (TRAIN_RATIO + VALIDATION_RATIO)))
    train_days = set(unique_days[:train_end_index])
    validation_days = set(unique_days[train_end_index:validation_end_index])
    test_days = set(unique_days[validation_end_index:])

    train_frame = dataframe[dataframe["event_day"].isin(train_days)].reset_index(drop=True)
    validation_frame = dataframe[dataframe["event_day"].isin(validation_days)].reset_index(drop=True)
    test_frame = dataframe[dataframe["event_day"].isin(test_days)].reset_index(drop=True)
    if validation_frame.empty or test_frame.empty:
        raise ValueError("Validation or test split is empty; provide more days of data.")

    contamination = _estimate_contamination(train_frame)
    validation_eval = _inject_synthetic_anomalies(validation_frame, feature_columns, random_seed + 1)
    test_eval = _inject_synthetic_anomalies(test_frame, feature_columns, random_seed + 2)

    scaler = RobustScaler()
    x_train = scaler.fit_transform(train_frame[feature_columns])
    x_validation = scaler.transform(validation_eval["features"][feature_columns])
    x_test = scaler.transform(test_eval["features"][feature_columns])

    return {
        "train_frame": train_frame,
        "validation_frame": validation_frame,
        "test_frame": test_frame,
        "validation_eval": validation_eval,
        "test_eval": test_eval,
        "feature_columns": feature_columns,
        "scaler": scaler,
        "x_train": x_train,
        "x_validation": x_validation,
        "x_test": x_test,
        "y_validation": validation_eval["labels"],
        "y_test": test_eval["labels"],
        "contamination": contamination,
    }


def train_models(
    x_train: np.ndarray,
    contamination: float,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Train baseline versions of each anomaly detector."""

    models = {
        "IsolationForest": IsolationForest(
            n_estimators=300,
            max_samples="auto",
            contamination=contamination,
            random_state=random_seed,
            n_jobs=-1,
        ),
        "OneClassSVM": OneClassSVM(kernel="rbf", gamma="scale", nu=max(contamination, 0.02)),
        "LocalOutlierFactor": LocalOutlierFactor(
            n_neighbors=max(2, min(35, len(x_train) - 1)),
            contamination=contamination,
            novelty=True,
        ),
        "HBOS": HBOS(contamination=contamination),
    }
    for model_name, model in models.items():
        LOGGER.info("Training baseline model: %s", model_name)
        model.fit(x_train)
    return models


def tune_hyperparameters(
    x_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    contamination: float,
    random_seed: int = RANDOM_SEED,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Tune anomaly models using synthetic anomaly validation and time-aware stability."""

    parameter_spaces = {
        "IsolationForest": _unique_param_grid(
            {
                "n_estimators": [200, 400],
                "max_samples": [0.7, 1.0],
                "contamination": [contamination, min(0.08, contamination * 1.5)],
            }
        ),
        "OneClassSVM": _unique_param_grid(
            {
                "nu": [max(0.01, contamination), min(0.1, contamination * 2)],
                "gamma": ["scale", 0.05, 0.1],
            }
        ),
        "LocalOutlierFactor": _unique_param_grid(
            {
                "n_neighbors": [20, 35, 50],
                "contamination": [contamination],
            }
        ),
        "HBOS": _unique_param_grid({"n_bins": [8, 12, 16], "contamination": [contamination]}),
    }

    best_models: dict[str, Any] = {}
    tuning_rows: list[dict[str, Any]] = []

    for model_name, candidates in parameter_spaces.items():
        LOGGER.info("Tuning %s across %s candidates", model_name, len(candidates))
        best_payload: dict[str, Any] | None = None
        for params in candidates:
            model = _build_model(model_name, params, contamination, random_seed, sample_count=len(x_train))
            model.fit(x_train)
            validation_scores = _compute_anomaly_scores(model_name, model, x_validation)
            fold_stability = _cross_validated_stability(model_name, params, x_train, contamination, random_seed)
            metrics = _score_predictions(y_validation, validation_scores, fold_stability)
            row = {
                "model_name": model_name,
                "params": params,
                **metrics,
            }
            tuning_rows.append(row)
            if best_payload is None or row["selection_score"] > best_payload["selection_score"]:
                best_payload = {
                    "model": model,
                    "params": params,
                    "selection_score": row["selection_score"],
                }
        if best_payload is None:
            raise RuntimeError(f"No tuning result produced for {model_name}")
        best_models[model_name] = best_payload

    tuning_results = pd.DataFrame(tuning_rows).sort_values(
        ["selection_score", "roc_auc"], ascending=[False, False]
    )
    return best_models, tuning_results


def evaluate_models(
    tuned_models: dict[str, Any],
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """Evaluate tuned models on validation and test sets and rank them."""

    comparison_rows: list[dict[str, Any]] = []
    details: dict[str, dict[str, Any]] = {}

    for model_name, payload in tuned_models.items():
        model = payload["model"]
        validation_scores = _compute_anomaly_scores(model_name, model, x_validation)
        test_scores = _compute_anomaly_scores(model_name, model, x_test)

        validation_metrics = _score_predictions(y_validation, validation_scores, stability=payload["selection_score"])
        test_metrics = _score_predictions(y_test, test_scores, stability=validation_metrics["stability"])
        importance_proxy = _feature_importance_proxy(model_name, model, x_validation, feature_columns)
        details[model_name] = {
            "validation_scores": validation_scores,
            "test_scores": test_scores,
            "feature_importance_proxy": importance_proxy,
            "best_params": payload["params"],
        }
        comparison_rows.append(
            {
                "model_name": model_name,
                "validation_roc_auc": validation_metrics["roc_auc"],
                "validation_average_precision": validation_metrics["average_precision"],
                "test_roc_auc": test_metrics["roc_auc"],
                "test_average_precision": test_metrics["average_precision"],
                "test_silhouette": test_metrics["silhouette_separation"],
                "test_reconstruction_consistency": test_metrics["reconstruction_consistency"],
                "score_mean": float(np.mean(test_scores)),
                "score_std": float(np.std(test_scores)),
                "score_p95": float(np.percentile(test_scores, 95)),
                "selection_score": test_metrics["selection_score"],
            }
        )

    comparison = pd.DataFrame(comparison_rows).sort_values(
        ["selection_score", "test_roc_auc"], ascending=[False, False]
    )
    return comparison, details


def save_best_model(
    model_name: str,
    model: Any,
    scaler: RobustScaler,
    feature_columns: list[str],
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    """Persist the selected model and preprocessing artifacts for inference."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model_path = output_path / "best_anomaly_model.pkl"
    scaler_path = output_path / "scaler.pkl"
    feature_columns_path = output_path / "feature_columns.json"

    joblib.dump({"model_name": model_name, "model": model}, model_path)
    joblib.dump(scaler, scaler_path)
    with feature_columns_path.open("w", encoding="utf-8") as handle:
        json.dump(feature_columns, handle, indent=2)

    LOGGER.info("Saved model artifacts to %s", output_path)
    return model_path, scaler_path, feature_columns_path


def run_training_pipeline(
    data_path: str | Path,
    output_dir: str | Path | None = None,
) -> TrainingArtifacts:
    """Execute the complete production training pipeline."""

    raw_logs = load_data(data_path)
    normalized_logs = normalize_logs(raw_logs)
    features, feature_columns = build_features(normalized_logs)
    split_payload = split_dataset(features, feature_columns)
    _ = train_models(split_payload["x_train"], split_payload["contamination"])
    tuned_models, tuning_results = tune_hyperparameters(
        split_payload["x_train"],
        split_payload["x_validation"],
        split_payload["y_validation"],
        split_payload["contamination"],
    )
    comparison, details = evaluate_models(
        tuned_models=tuned_models,
        x_validation=split_payload["x_validation"],
        y_validation=split_payload["y_validation"],
        x_test=split_payload["x_test"],
        y_test=split_payload["y_test"],
        feature_columns=feature_columns,
    )

    best_row = comparison.iloc[0]
    best_name = str(best_row["model_name"])
    best_model = tuned_models[best_name]["model"]
    best_params = details[best_name]["best_params"]

    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[2] / "saved_models"
    model_path, scaler_path, feature_columns_path = save_best_model(
        model_name=best_name,
        model=best_model,
        scaler=split_payload["scaler"],
        feature_columns=feature_columns,
        output_dir=output_dir,
    )

    LOGGER.info("Best model selected: %s | params=%s", best_name, best_params)
    LOGGER.info("Model comparison:\n%s", comparison.to_string(index=False))
    LOGGER.info("Tuning summary (top 10):\n%s", tuning_results.head(10).to_string(index=False))

    return TrainingArtifacts(
        model_name=best_name,
        model_path=model_path,
        scaler_path=scaler_path,
        feature_columns_path=feature_columns_path,
        comparison=comparison,
        feature_columns=feature_columns,
        best_params=best_params,
    )


def _resolve_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
    required: bool = True,
) -> str | None:
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate
    if required:
        raise KeyError(f"Required column not found. Expected one of: {candidates}")
    return None


def _series_or_default(dataframe: pd.DataFrame, column: str | None, default_value: str) -> pd.Series:
    if column is None:
        return pd.Series(default_value, index=dataframe.index, dtype="object")
    return dataframe[column].astype(str).fillna(default_value).replace({"": default_value})


def _normalize_activity(activity_series: pd.Series) -> pd.Series:
    normalized = activity_series.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False)
    return normalized.map(
        lambda value: "login_success"
        if "logon" in value or "login" in value
        else ("logout" if "logoff" in value or "logout" in value else value)
    )


def _derive_event_category(event_type: str) -> str:
    if event_type in {"login_success", "login_failed", "logout"}:
        return "authentication"
    if "file" in event_type:
        return "data_access"
    if "email" in event_type:
        return "communication"
    if "process" in event_type:
        return "endpoint"
    return "activity"


def _derive_event_source(event_type: str) -> str:
    if event_type in {"login_success", "login_failed", "logout"}:
        return "IAM"
    if "email" in event_type:
        return "Email"
    if "file" in event_type:
        return "EDR"
    return "EDR"


def _estimate_contamination(train_frame: pd.DataFrame) -> float:
    suspicious_proxy = (
        (train_frame["after_hours_activity_ratio"] > 0.25)
        | (train_frame["device_switch_rate"] > 0.35)
        | (train_frame["abnormal_login_hour_score"] > 3.0)
    )
    contamination = float(np.clip(suspicious_proxy.mean(), 0.01, 0.08))
    LOGGER.info("Estimated contamination at %.4f", contamination)
    return contamination if contamination > 0 else DEFAULT_CONTAMINATION


def _unique_param_grid(grid_spec: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Build a deterministic parameter grid without duplicate combinations."""

    unique: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()
    for params in ParameterGrid(grid_spec):
        key = tuple(sorted(params.items()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(params))
    return unique


def _inject_synthetic_anomalies(
    base_frame: pd.DataFrame,
    feature_columns: list[str],
    random_seed: int,
) -> dict[str, Any]:
    """Inject plausible synthetic anomalies for validation/test scoring."""

    rng = np.random.default_rng(random_seed)
    anomaly_count = max(10, int(len(base_frame) * SYNTHETIC_ANOMALY_RATE))
    anomaly_source = base_frame.sample(
        n=min(anomaly_count, len(base_frame)),
        replace=len(base_frame) < anomaly_count,
        random_state=random_seed,
    ).copy()

    anomaly_source["login_frequency_per_day"] *= rng.uniform(1.8, 3.4, len(anomaly_source))
    anomaly_source["after_hours_activity_ratio"] = np.clip(
        anomaly_source["after_hours_activity_ratio"] + rng.uniform(0.35, 0.9, len(anomaly_source)),
        0.0,
        1.0,
    )
    anomaly_source["weekend_activity_ratio"] = np.clip(
        anomaly_source["weekend_activity_ratio"] + rng.uniform(0.25, 0.8, len(anomaly_source)),
        0.0,
        1.0,
    )
    anomaly_source["session_duration_estimate"] *= rng.uniform(1.5, 2.5, len(anomaly_source))
    anomaly_source["unique_devices_used"] = np.ceil(
        anomaly_source["unique_devices_used"] + rng.integers(2, 5, len(anomaly_source))
    )
    anomaly_source["unique_activity_types"] = np.ceil(
        anomaly_source["unique_activity_types"] + rng.integers(1, 4, len(anomaly_source))
    )
    anomaly_source["device_switch_rate"] = np.clip(
        anomaly_source["device_switch_rate"] + rng.uniform(0.35, 0.7, len(anomaly_source)),
        0.0,
        1.0,
    )
    anomaly_source["mean_time_between_logins"] *= rng.uniform(0.08, 0.4, len(anomaly_source))
    anomaly_source["login_time_variance"] += rng.uniform(2.5, 8.0, len(anomaly_source))
    anomaly_source["activity_entropy"] += rng.uniform(0.4, 1.6, len(anomaly_source))
    anomaly_source["abnormal_login_hour_score"] += rng.uniform(3.0, 8.0, len(anomaly_source))
    anomaly_source["host_change_frequency"] = np.clip(
        anomaly_source["host_change_frequency"] + rng.uniform(0.25, 0.7, len(anomaly_source)),
        0.0,
        1.0,
    )

    normal_features = base_frame[feature_columns].copy()
    anomaly_features = anomaly_source[feature_columns].copy()
    combined = pd.concat([normal_features, anomaly_features], ignore_index=True)
    labels = np.concatenate(
        [
            np.zeros(len(normal_features), dtype=np.int8),
            np.ones(len(anomaly_features), dtype=np.int8),
        ]
    )
    return {"features": combined, "labels": labels}


def _build_model(
    model_name: str,
    params: dict[str, Any],
    contamination: float,
    random_seed: int,
    sample_count: int | None = None,
) -> Any:
    if model_name == "IsolationForest":
        return IsolationForest(random_state=random_seed, n_jobs=-1, **params)
    if model_name == "OneClassSVM":
        return OneClassSVM(kernel="rbf", **params)
    if model_name == "LocalOutlierFactor":
        effective_params = dict(params)
        if sample_count is not None:
            effective_params["n_neighbors"] = max(2, min(int(effective_params["n_neighbors"]), sample_count - 1))
        return LocalOutlierFactor(novelty=True, **effective_params)
    if model_name == "HBOS":
        return HBOS(**params)
    raise ValueError(f"Unsupported model name: {model_name}")


def _compute_anomaly_scores(model_name: str, model: Any, features: np.ndarray) -> np.ndarray:
    if model_name == "HBOS":
        scores = np.asarray(model.decision_function(features), dtype=float)
    else:
        scores = -np.asarray(model.score_samples(features), dtype=float)
    return np.nan_to_num(scores, copy=False, nan=0.0, posinf=1e6, neginf=-1e6)


def _cross_validated_stability(
    model_name: str,
    params: dict[str, Any],
    x_train: np.ndarray,
    contamination: float,
    random_seed: int,
) -> float:
    """Estimate training stability across time-aware folds.

    Higher is better. The metric rewards models whose anomaly rate on holdout
    normal folds remains stable instead of oscillating wildly.
    """

    if len(x_train) < 30:
        return 0.5

    splitter = TimeSeriesSplit(n_splits=min(4, max(2, len(x_train) // 50)))
    anomaly_rates: list[float] = []
    for train_index, holdout_index in splitter.split(x_train):
        fold_model = _build_model(
            model_name,
            params,
            contamination,
            random_seed,
            sample_count=len(train_index),
        )
        fold_model.fit(x_train[train_index])
        fold_scores = _compute_anomaly_scores(model_name, fold_model, x_train[holdout_index])
        threshold = float(np.quantile(fold_scores, 1.0 - contamination))
        anomaly_rates.append(float((fold_scores >= threshold).mean()))

    rate_std = float(np.std(anomaly_rates)) if anomaly_rates else 1.0
    return float(np.clip(1.0 - rate_std / max(contamination, 1e-3), 0.0, 1.0))


def _score_predictions(
    labels: np.ndarray,
    scores: np.ndarray,
    stability: float,
) -> dict[str, float]:
    roc_auc = float(roc_auc_score(labels, scores))
    average_precision = float(average_precision_score(labels, scores))
    silhouette = _safe_silhouette(scores, labels)
    reconstruction_consistency = _reconstruction_consistency(scores)
    selection_score = (
        0.4 * roc_auc
        + 0.2 * average_precision
        + 0.15 * silhouette
        + 0.15 * reconstruction_consistency
        + 0.1 * stability
    )
    return {
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "silhouette_separation": silhouette,
        "reconstruction_consistency": reconstruction_consistency,
        "stability": float(stability),
        "selection_score": float(selection_score),
    }


def _safe_silhouette(scores: np.ndarray, labels: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return 0.0
    try:
        return float(silhouette_score(scores.reshape(-1, 1), labels))
    except Exception:
        return 0.0


def _reconstruction_consistency(scores: np.ndarray) -> float:
    if len(scores) < 10:
        return 0.0
    shifted = pd.Series(scores).rolling(window=5, min_periods=1).mean().to_numpy()
    if np.std(scores) == 0 or np.std(shifted) == 0:
        return 0.0
    correlation = np.corrcoef(scores, shifted)[0, 1]
    if np.isnan(correlation):
        return 0.0
    return float(np.clip((correlation + 1.0) / 2.0, 0.0, 1.0))


def _feature_importance_proxy(
    model_name: str,
    model: Any,
    features: np.ndarray,
    feature_columns: list[str],
) -> dict[str, float]:
    """Estimate feature influence by measuring score drift under permutation."""

    baseline_scores = _compute_anomaly_scores(model_name, model, features)
    rng = np.random.default_rng(RANDOM_SEED)
    importance: dict[str, float] = {}
    sample_size = min(len(features), 5000)
    sample = features[:sample_size].copy()
    baseline_sample_scores = baseline_scores[:sample_size]

    for index, feature_name in enumerate(feature_columns):
        perturbed = sample.copy()
        rng.shuffle(perturbed[:, index])
        shifted_scores = _compute_anomaly_scores(model_name, model, perturbed)
        importance[feature_name] = float(np.mean(np.abs(shifted_scores - baseline_sample_scores)))
    return dict(sorted(importance.items(), key=lambda item: item[1], reverse=True))
