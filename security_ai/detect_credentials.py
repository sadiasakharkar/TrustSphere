"""Inference utility for credential exposure detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from security_ai.features.credential_exposure_features import CredentialFeatureEngineer

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "artifacts" / "credential_detector.pkl"


class CredentialExposurePredictor:
    def __init__(self, model_path: str | Path = MODEL_PATH) -> None:
        self.model = joblib.load(model_path)
        self.feature_engineer = CredentialFeatureEngineer()

    def predict(self, text: str, commit_message: str = "", paste_context: str = "") -> dict:
        dataset = self.feature_engineer.build_dataset([
            {"text": text, "commit_message": commit_message, "paste_context": paste_context, "label": 0}
        ])
        artifacts = self.feature_engineer.build_features(dataset)
        probability = float(self.model.predict_proba(artifacts.dataframe[artifacts.feature_columns])[:, 1][0])
        regex_weight = float(artifacts.dataframe["regex_match_weight"].iloc[0])
        context_risk = float(artifacts.dataframe["context_risk"].iloc[0])
        ner_confidence = 0.0
        risk_score = round(regex_weight + ner_confidence + context_risk + (probability * 2.0), 4)
        return {
            "credential_exposed": int(probability >= 0.5),
            "probability": probability,
            "risk_score": risk_score,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--commit-message", default="")
    parser.add_argument("--paste-context", default="")
    args = parser.parse_args()
    predictor = CredentialExposurePredictor()
    print(json.dumps(predictor.predict(args.text, args.commit_message, args.paste_context), indent=2))
