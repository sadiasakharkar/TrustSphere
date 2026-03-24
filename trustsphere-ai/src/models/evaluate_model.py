"""Evaluation utilities for TrustSphere anomaly detection models."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, silhouette_score

try:
    from .config import ARTIFACTS_DIR, MODEL_VERSION, TOP_K_FRACTION
except ImportError:
    from config import ARTIFACTS_DIR, MODEL_VERSION, TOP_K_FRACTION

LOGGER = logging.getLogger(__name__)


def evaluate_model(
    model_name: str,
    anomaly_scores: np.ndarray,
    labels: np.ndarray | None,
    transformed_features: np.ndarray,
    thresholds: dict[str, float],
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compute model metrics for anomaly detection outputs."""
    scores = np.asarray(anomaly_scores, dtype=float)
    threshold = float(thresholds.get("anomaly_threshold", np.quantile(scores, 0.95)))
    predicted = (scores >= threshold).astype(int)
    top_k = max(1, int(len(scores) * TOP_K_FRACTION))

    metrics: dict[str, Any] = {
        "score_mean": float(np.mean(scores)),
        "score_std": float(np.std(scores)),
        "score_p95": float(np.percentile(scores, 95)),
        "score_p99": float(np.percentile(scores, 99)),
        "silhouette_proxy": _safe_silhouette(transformed_features, predicted),
        "precision_at_k": _precision_at_k(scores, labels, top_k),
        "false_positive_rate": _false_positive_rate(predicted, labels),
    }

    if labels is not None and len(np.unique(labels)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(labels, scores))
        metrics["pr_auc"] = float(average_precision_score(labels, scores))
        precision, recall, _ = precision_recall_curve(labels, scores)
        metrics["pr_curve_points"] = {
            "precision": precision[:50].round(6).tolist(),
            "recall": recall[:50].round(6).tolist(),
        }
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
        metrics["pr_curve_points"] = {"precision": [], "recall": []}

    report = {
        "model_version": MODEL_VERSION,
        "model_name": model_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": thresholds,
        "metrics": metrics,
    }
    destination = Path(report_path) if report_path else ARTIFACTS_DIR / "model_report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOGGER.info("Saved model report to %s", destination)
    return report


def _safe_silhouette(features: np.ndarray, labels: np.ndarray) -> float:
    try:
        if len(np.unique(labels)) < 2 or len(features) < 10:
            return 0.0
        return float(silhouette_score(features, labels))
    except Exception:
        return 0.0


def _precision_at_k(scores: np.ndarray, labels: np.ndarray | None, top_k: int) -> float | None:
    if labels is None or len(np.unique(labels)) < 2:
        return None
    top_indices = np.argsort(scores)[::-1][:top_k]
    return float(np.mean(labels[top_indices]))


def _false_positive_rate(predicted: np.ndarray, labels: np.ndarray | None) -> float | None:
    if labels is None or len(np.unique(labels)) < 2:
        return None
    negatives = labels == 0
    if negatives.sum() == 0:
        return None
    return float(((predicted == 1) & negatives).sum() / negatives.sum())
