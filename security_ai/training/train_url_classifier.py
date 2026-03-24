"""Training pipeline for URL phishing detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from security_ai.features.url_phishing_features import URLPhishingFeatureEngineer
from security_ai.models.url_classifier import URLPhishingModel, XGBOOST_AVAILABLE

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "url_model.json"
SCHEMA_PATH = ARTIFACTS_DIR / "feature_schema.json"
SCALER_PATH = ARTIFACTS_DIR / "url_scaler.joblib"

try:
    import optuna
    OPTUNA_AVAILABLE = True
except Exception:
    optuna = None
    OPTUNA_AVAILABLE = False


def train_url_classifier() -> dict:
    engineer = URLPhishingFeatureEngineer()
    dataset = engineer.build_dataset()
    artifacts = engineer.build_features(dataset)
    x_values = artifacts.dataframe[artifacts.feature_columns].astype(float)
    y_values = artifacts.dataframe["label"].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(x_values, y_values, test_size=0.3, random_state=42, stratify=y_values)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    best_params = _optimize_parameters(x_train_scaled, y_train, x_test_scaled, y_test)
    model = URLPhishingModel(best_params)
    model.fit(x_train_scaled, y_train)
    probabilities = model.predict_proba(x_test_scaled)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if len(np.unique(y_test)) > 1 else 0.0,
        "precision_phishing": float(precision_score(y_test, predicted, zero_division=0)),
        "false_positive_rate": float(((predicted == 1) & (y_test.to_numpy() == 0)).sum() / max(1, int((y_test.to_numpy() == 0).sum()))),
    }
    metadata = {"model_type": model.model_type, "xgboost_available": XGBOOST_AVAILABLE, "optuna_available": OPTUNA_AVAILABLE, "best_params": best_params, "metrics": metrics}
    model.save(MODEL_PATH, metadata)
    SCHEMA_PATH.write_text(json.dumps(artifacts.feature_columns, indent=2), encoding="utf-8")
    joblib.dump(scaler, SCALER_PATH)
    return metadata


def _optimize_parameters(x_train, y_train, x_test, y_test) -> dict:
    if OPTUNA_AVAILABLE:
        def objective(trial):
            params = {
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.3, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            }
            model = URLPhishingModel(params)
            model.fit(x_train, y_train)
            scores = model.predict_proba(x_test)[:, 1]
            return roc_auc_score(y_test, scores) if len(np.unique(y_test)) > 1 else 0.5
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=12)
        return study.best_params
    best_params = None
    best_score = -1.0
    for params in [
        {"max_depth": 3, "learning_rate": 0.1, "n_estimators": 150},
        {"max_depth": 4, "learning_rate": 0.05, "n_estimators": 250},
        {"max_depth": 5, "learning_rate": 0.08, "n_estimators": 300},
    ]:
        model = URLPhishingModel(params)
        model.fit(x_train, y_train)
        scores = model.predict_proba(x_test)[:, 1]
        metric = roc_auc_score(y_test, scores) if len(np.unique(y_test)) > 1 else 0.5
        if metric > best_score:
            best_score = metric
            best_params = params
    return best_params or {"max_depth": 3, "learning_rate": 0.1, "n_estimators": 150}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_url_classifier(), indent=2))
