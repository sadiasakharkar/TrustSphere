"""Evaluation utilities for offline anomaly models."""

from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, silhouette_score

try:
    from .config import ARTIFACTS_DIR, MODEL_VERSION
except ImportError:
    from config import ARTIFACTS_DIR, MODEL_VERSION


LOGGER = logging.getLogger(__name__)


def evaluate_model(
    model_name: str,
    scores: np.ndarray,
    labels: np.ndarray | None,
    transformed_features: np.ndarray,
    feature_columns: list[str],
    training_rows: int,
    anomaly_ratio: float,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compute unsupervised and optional supervised evaluation metrics."""
    metrics: dict[str, Any] = {
        "score_mean": float(np.mean(scores)),
        "score_std": float(np.std(scores)),
        "score_p95": float(np.percentile(scores, 95)),
        "score_p99": float(np.percentile(scores, 99)),
        "silhouette_proxy": _safe_silhouette(scores),
        "feature_variance_contribution": float(np.mean(np.var(transformed_features, axis=0))),
        "reconstruction_stability": _reconstruction_stability(scores),
    }

    if labels is not None and len(np.unique(labels)) > 1:
        binary_predictions = (scores >= np.quantile(scores, 0.95)).astype(int)
        metrics.update(
            {
                "roc_auc": float(roc_auc_score(labels, scores)),
                "precision": float(precision_score(labels, binary_predictions, zero_division=0)),
                "recall": float(recall_score(labels, binary_predictions, zero_division=0)),
                "f1_score": float(f1_score(labels, binary_predictions, zero_division=0)),
            }
        )

    report = {
        "model_version": MODEL_VERSION,
        "model_name": model_name,
        "feature_count": len(feature_columns),
        "training_rows": int(training_rows),
        "anomaly_ratio": float(anomaly_ratio),
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
    }

    if report_path is None:
        report_path = ARTIFACTS_DIR / "model_report.json"
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    LOGGER.info("Saved model report to %s", report_path)
    return report


def _safe_silhouette(scores: np.ndarray) -> float:
    try:
        threshold = np.quantile(scores, 0.95)
        labels = (scores >= threshold).astype(int)
        if len(np.unique(labels)) < 2:
            return 0.0
        return float(silhouette_score(scores.reshape(-1, 1), labels))
    except Exception:
        return 0.0


def _reconstruction_stability(scores: np.ndarray) -> float:
    if len(scores) < 10:
        return 0.0
    rolling = pd.Series(scores).rolling(window=10, min_periods=1).mean().to_numpy()
    correlation = np.corrcoef(scores, rolling)[0, 1]
    if np.isnan(correlation):
        return 0.0
    return float((correlation + 1.0) / 2.0)
