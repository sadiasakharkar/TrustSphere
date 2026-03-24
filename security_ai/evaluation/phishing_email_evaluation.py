"""Evaluation helpers for phishing email detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

LOGGER = logging.getLogger(__name__)


def compute_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    predicted = (probabilities >= 0.5).astype(int)
    metrics = {
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "precision_phishing": float(precision_score(labels, predicted, zero_division=0)),
        "recall_phishing": float(recall_score(labels, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) > 1 else 0.0,
    }
    return metrics


def save_evaluation(metrics: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    LOGGER.info("Saved phishing email evaluation to %s", path)
    return path
