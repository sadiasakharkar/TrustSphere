"""Training pipeline for TrustSphere credential exposure detector."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

from security_ai.features.credential_exposure_features import CredentialFeatureEngineer
from security_ai.models.credential_detector import RegexContextCredentialDetector, SpacyCredentialTrainer, SPACY_AVAILABLE, classification_report

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "credential_detector.pkl"
RULES_PATH = ARTIFACTS_DIR / "rules.yaml"
NER_DIR = ARTIFACTS_DIR / "credential_ner"


def train_credential_detector() -> dict:
    feature_engineer = CredentialFeatureEngineer()
    dataset = feature_engineer.build_dataset()
    artifacts = feature_engineer.build_features(dataset)
    x_values = artifacts.dataframe[artifacts.feature_columns]
    y_values = artifacts.dataframe["label"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x_values, y_values, test_size=0.34, random_state=42, stratify=y_values)

    detector = RegexContextCredentialDetector()
    detector.fit(x_train, y_train)
    probabilities = detector.predict_proba(x_test)[:, 1]
    metrics = classification_report(y_test.to_numpy(), probabilities)
    detector.save(MODEL_PATH)
    feature_engineer.export_rules(RULES_PATH)

    result = {
        "metrics": metrics,
        "model_path": str(MODEL_PATH),
        "rules_path": str(RULES_PATH),
        "ner_ready": False,
    }
    if SPACY_AVAILABLE:
        try:
            trainer = SpacyCredentialTrainer()
            training_examples = [
                ("api_token = AKIA1234567890ABCDEF", {"entities": [(12, 32, "TOKEN")]}),
                ("password=Password123", {"entities": [(9, 20, "CREDENTIAL")]}),
                ("-----BEGIN PRIVATE KEY-----", {"entities": [(0, 27, "SECRET")]}),
            ]
            result["ner"] = trainer.train(training_examples, NER_DIR)
            result["ner_ready"] = True
        except Exception as exc:
            LOGGER.warning("spaCy NER training skipped: %s", exc)
    (ARTIFACTS_DIR / "credential_detector_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_credential_detector(), indent=2))
