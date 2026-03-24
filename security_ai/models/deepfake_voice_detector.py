"""Voice deepfake detection models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.svm import SVC


class DeepfakeVoiceBaseline:
    """Runnable SVM baseline for deepfake voice detection."""

    def __init__(self, kernel: str = "rbf", probability: bool = True) -> None:
        self.model = SVC(kernel=kernel, probability=probability, class_weight="balanced")

    def fit(self, x_train, y_train) -> None:
        self.model.fit(x_train, y_train)

    def predict_proba(self, x_values) -> np.ndarray:
        return self.model.predict_proba(x_values)

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        return path


class DeepfakeVoiceCNNPlaceholder:
    """Optional CNN path for environments with PyTorch installed."""

    def save_placeholder(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PyTorch CNN model export requires torch in this environment.\n")
        return path
