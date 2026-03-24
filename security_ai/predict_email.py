"""Inference entrypoint for phishing email prediction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from security_ai.config import MODEL_EXPORT_DIR
from security_ai.features.phishing_email_features import PhishingEmailFeatureEngineer


class EmailPredictor:
    def __init__(self, model_dir: str | Path = MODEL_EXPORT_DIR) -> None:
        self.model_dir = Path(model_dir)
        self.model = joblib.load(self.model_dir / "model.joblib")
        self.feature_engineer = PhishingEmailFeatureEngineer()

    def predict(self, subject: str, body: str, sender: str, attachments: str = "") -> dict:
        frame = pd.DataFrame([
            {"subject": subject, "email_body": body, "sender": sender, "attachments": attachments, "label": 0}
        ])
        prepared = self.feature_engineer.build_features(frame).dataframe
        probability = float(self.model.predict_proba(prepared)[:, 1][0])
        label = int(probability >= 0.5)
        return {"phishing_probability": probability, "prediction": label}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--sender", required=True)
    parser.add_argument("--attachments", default="")
    args = parser.parse_args()
    predictor = EmailPredictor()
    print(json.dumps(predictor.predict(args.subject, args.body, args.sender, args.attachments), indent=2))
