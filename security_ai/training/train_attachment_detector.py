"""Training pipeline for malicious attachment detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from security_ai.features.attachment_features import AttachmentFeatureEngineer
from security_ai.models.attachment_detector import AttachmentRiskModel

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "attachment_detector.pkl"
SCALER_PATH = ARTIFACTS_DIR / "attachment_scaler.joblib"


def train_attachment_detector() -> dict:
    engineer = AttachmentFeatureEngineer()
    dataset = engineer.build_dataset()
    artifacts = engineer.build_features(dataset)
    x_values = artifacts.dataframe[artifacts.feature_columns].astype(float)
    y_values = artifacts.dataframe["label"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x_values, y_values, test_size=0.34, random_state=42, stratify=y_values)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = AttachmentRiskModel()
    model.fit(x_train_scaled)
    anomaly_scores = model.score(x_test_scaled)
    heuristic = _heuristic_risk(artifacts.dataframe.loc[x_test.index])
    attachment_risk_score = np.clip((0.6 * anomaly_scores + 0.4 * heuristic) * 100.0, 0, 100)
    malware_probability = np.clip(0.7 * anomaly_scores + 0.3 * heuristic, 0.0, 1.0)
    result = {
        "attachment_risk_score": attachment_risk_score.round(4).tolist(),
        "malware_probability": malware_probability.round(4).tolist(),
        "feature_columns": artifacts.feature_columns,
    }
    model.save(MODEL_PATH)
    import joblib
    joblib.dump(scaler, SCALER_PATH)
    (ARTIFACTS_DIR / "attachment_detector_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _heuristic_risk(frame) -> np.ndarray:
    score = (
        0.2 * frame["macro_presence"].to_numpy(dtype=float)
        + 0.2 * frame["extension_mismatch"].to_numpy(dtype=float)
        + 0.2 * frame["execution_after_download"].to_numpy(dtype=float)
        + 0.2 * frame["privilege_escalation_behavior"].to_numpy(dtype=float)
        + 0.1 * frame["double_extension"].to_numpy(dtype=float)
        + 0.1 * frame["embedded_script_hint"].to_numpy(dtype=float)
    )
    return np.clip(score, 0.0, 1.0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_attachment_detector(), indent=2))
