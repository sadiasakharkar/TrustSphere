"""Inference utility for URL phishing classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from security_ai.features.url_phishing_features import URLPhishingFeatureEngineer

BASE_DIR = Path(__file__).resolve().parent
MODEL_JSON = BASE_DIR / "artifacts" / "url_model.json"
SCHEMA_PATH = BASE_DIR / "artifacts" / "feature_schema.json"
SCALER_PATH = BASE_DIR / "artifacts" / "url_scaler.joblib"


class URLPhishingPredictor:
    def __init__(self, model_json: str | Path = MODEL_JSON) -> None:
        self.model_json = Path(model_json)
        payload = json.loads(self.model_json.read_text(encoding="utf-8")) if self.model_json.exists() else {}
        joblib_path = payload.get("joblib_path")
        if joblib_path:
            self.model = joblib.load(joblib_path)
        else:
            raise FileNotFoundError("URL classifier fallback joblib artifact is required in this environment.")
        self.scaler = joblib.load(SCALER_PATH)
        self.feature_engineer = URLPhishingFeatureEngineer()
        self.feature_columns = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def predict(self, url: str) -> dict:
        dataset = self.feature_engineer.build_dataset([{"url": url, "label": 0}])
        artifacts = self.feature_engineer.build_features(dataset)
        features = artifacts.dataframe[self.feature_columns].astype(float)
        transformed = self.scaler.transform(features)
        probability = float(self.model.predict_proba(transformed)[:, 1][0])
        return {"url": url, "phishing_probability": probability, "prediction": int(probability >= 0.5)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    print(json.dumps(URLPhishingPredictor().predict(args.url), indent=2))
