"""Training pipeline for deepfake voice detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from security_ai.features.deepfake_voice_features import DeepfakeVoiceFeatureEngineer
from security_ai.models.deepfake_voice_detector import DeepfakeVoiceBaseline, DeepfakeVoiceCNNPlaceholder

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "deepfake_voice_model.pt"
SVM_PATH = ARTIFACTS_DIR / "deepfake_voice_model.joblib"
SCALER_PATH = ARTIFACTS_DIR / "deepfake_voice_scaler.joblib"


def train_deepfake_voice_detector() -> dict:
    engineer = DeepfakeVoiceFeatureEngineer()
    dataset = engineer.build_dataset()
    artifacts = engineer.build_features(dataset)
    x_values = artifacts.dataframe[artifacts.feature_columns].astype(float)
    y_values = artifacts.dataframe["label"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x_values, y_values, test_size=0.34, random_state=42, stratify=y_values)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = DeepfakeVoiceBaseline()
    model.fit(x_train_scaled, y_train)
    probabilities = model.predict_proba(x_test_scaled)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)

    fpr, tpr, thresholds = roc_curve(y_test, probabilities)
    fnr = 1 - tpr
    eer_index = np.nanargmin(np.abs(fnr - fpr))
    eer = float((fpr[eer_index] + fnr[eer_index]) / 2.0)
    accuracy = float(accuracy_score(y_test, predicted))

    import joblib
    joblib.dump(scaler, SCALER_PATH)
    model.save(SVM_PATH)
    DeepfakeVoiceCNNPlaceholder().save_placeholder(MODEL_PATH)

    result = {
        "eer": eer,
        "accuracy": accuracy,
        "feature_columns": artifacts.feature_columns,
        "exported_model": str(MODEL_PATH),
        "baseline_model": str(SVM_PATH),
    }
    (ARTIFACTS_DIR / "deepfake_voice_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_deepfake_voice_detector(), indent=2))
