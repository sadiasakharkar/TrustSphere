"""Attachment risk model for TrustSphere."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


class AttachmentRiskModel:
    """Isolation Forest plus heuristic scoring wrapper."""

    def __init__(self, contamination: float = 0.15, random_state: int = 42) -> None:
        self.model = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)

    def fit(self, x_train) -> None:
        self.model.fit(x_train)

    def score(self, x_values) -> np.ndarray:
        raw = -self.model.score_samples(x_values)
        if np.allclose(raw.max(), raw.min()):
            return np.zeros_like(raw)
        return (raw - raw.min()) / (raw.max() - raw.min())

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        return path
