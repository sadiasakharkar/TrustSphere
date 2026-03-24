"""Inference utility for malicious attachment detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np

from security_ai.features.attachment_features import AttachmentFeatureEngineer
from security_ai.training.train_attachment_detector import _heuristic_risk

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "artifacts" / "attachment_detector.pkl"
SCALER_PATH = BASE_DIR / "artifacts" / "attachment_scaler.joblib"


class AttachmentPredictor:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.engineer = AttachmentFeatureEngineer()

    def predict(self, filename: str, size_bytes: int, content_text: str = "", event_context: str = "", post_download_action: str = "") -> dict:
        dataset = self.engineer.build_dataset([
            {
                "filename": filename,
                "size_bytes": size_bytes,
                "content_text": content_text,
                "event_context": event_context,
                "post_download_action": post_download_action,
                "label": 0,
            }
        ])
        artifacts = self.engineer.build_features(dataset)
        features = artifacts.dataframe[artifacts.feature_columns].astype(float)
        transformed = self.scaler.transform(features)
        raw = -self.model.score_samples(transformed)
        anomaly_score = float(1.0 / (1.0 + np.exp(-raw[0])))
        heuristic = float(_heuristic_risk(artifacts.dataframe).iloc[0] if hasattr(_heuristic_risk(artifacts.dataframe), 'iloc') else _heuristic_risk(artifacts.dataframe)[0])
        attachment_risk_score = round(float(np.clip((0.6 * anomaly_score + 0.4 * heuristic) * 100.0, 0, 100)), 4)
        malware_probability = round(float(np.clip(0.7 * anomaly_score + 0.3 * heuristic, 0.0, 1.0)), 4)
        return {"attachment_risk_score": attachment_risk_score, "malware_probability": malware_probability}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", required=True)
    parser.add_argument("--size-bytes", type=int, required=True)
    parser.add_argument("--content-text", default="")
    parser.add_argument("--event-context", default="")
    parser.add_argument("--post-download-action", default="")
    args = parser.parse_args()
    predictor = AttachmentPredictor()
    print(json.dumps(predictor.predict(args.filename, args.size_bytes, args.content_text, args.event_context, args.post_download_action), indent=2))
