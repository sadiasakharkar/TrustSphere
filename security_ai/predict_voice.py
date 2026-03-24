"""Inference utility for deepfake voice detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from security_ai.features.deepfake_voice_features import DeepfakeVoiceFeatureEngineer

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "artifacts" / "deepfake_voice_model.joblib"
SCALER_PATH = BASE_DIR / "artifacts" / "deepfake_voice_scaler.joblib"


class DeepfakeVoicePredictor:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.engineer = DeepfakeVoiceFeatureEngineer()

    def predict(self, waveform: np.ndarray, sample_rate: int = 16000) -> dict:
        dataset = self.engineer.build_dataset([{"waveform": waveform, "sample_rate": sample_rate, "label": 0}])
        artifacts = self.engineer.build_features(dataset)
        features = artifacts.dataframe[artifacts.feature_columns].astype(float)
        transformed = self.scaler.transform(features)
        probability = float(self.model.predict_proba(transformed)[:, 1][0])
        return {"deepfake_probability": probability, "prediction": int(probability >= 0.5)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="synthetic")
    args = parser.parse_args()
    predictor = DeepfakeVoicePredictor()
    sample_rate = 16000
    t = np.linspace(0, 1.0, sample_rate, endpoint=False)
    waveform = 0.5 * np.sign(np.sin(2 * np.pi * 220 * t)) if args.mode == "synthetic" else 0.5 * np.sin(2 * np.pi * 220 * t)
    print(json.dumps(predictor.predict(waveform, sample_rate), indent=2))
