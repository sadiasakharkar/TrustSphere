"""Training pipeline for LLM prompt injection defense."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from security_ai.features.prompt_guard_features import PromptGuardFeatureEngineer
from security_ai.models.prompt_guard import PromptGuardClassifier, TRANSFORMER_AVAILABLE

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_DIR = ARTIFACTS_DIR / "prompt_guard_model"
RULES_PATH = ARTIFACTS_DIR / "rules.json"


def train_prompt_guard() -> dict:
    engineer = PromptGuardFeatureEngineer()
    dataset = engineer.build_dataset()
    artifacts = engineer.build_features(dataset)
    train_df, test_df = train_test_split(artifacts.dataframe, test_size=0.3, random_state=42, stratify=artifacts.dataframe["label"])

    classifier = PromptGuardClassifier()
    classifier.fit(train_df, train_df["label"])
    probabilities = classifier.predict_proba(test_df)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(test_df["label"], predicted)),
        "f1": float(f1_score(test_df["label"], predicted, zero_division=0)),
        "precision": float(precision_score(test_df["label"], predicted, zero_division=0)),
        "recall": float(recall_score(test_df["label"], predicted, zero_division=0)),
        "transformer_ready": TRANSFORMER_AVAILABLE,
    }
    classifier.save(MODEL_DIR)
    engineer.export_rules(RULES_PATH)
    (ARTIFACTS_DIR / "prompt_guard_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_prompt_guard(), indent=2))
