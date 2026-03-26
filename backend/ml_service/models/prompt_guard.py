"""Prompt injection detector and rule engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    TRANSFORMER_AVAILABLE = True
except Exception:
    AutoModelForSequenceClassification = None
    AutoTokenizer = None
    TRANSFORMER_AVAILABLE = False


class PromptGuardClassifier:
    """Classifier wrapper with transformer-ready metadata and runnable fallback."""

    def __init__(self) -> None:
        self.pipeline = Pipeline(
            steps=[
                (
                    "features",
                    ColumnTransformer(
                        transformers=[
                            ("text", TfidfVectorizer(max_features=2500, ngram_range=(1, 2)), "prompt"),
                            (
                                "meta",
                                Pipeline(steps=[("scale", StandardScaler(with_mean=False))]),
                                [
                                    "override_phrase_score",
                                    "role_change_score",
                                    "secret_probe_score",
                                    "hidden_command_score",
                                    "encoding_trick_score",
                                    "length",
                                    "special_char_ratio",
                                    "uppercase_ratio",
                                ],
                            ),
                        ]
                    ),
                ),
                ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")),
            ]
        )

    def fit(self, x_train, y_train) -> None:
        self.pipeline.fit(x_train, y_train)

    def predict_proba(self, x_values) -> np.ndarray:
        return self.pipeline.predict_proba(x_values)

    def save(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path / "model.joblib")
        return path / "model.joblib"


class PromptRuleEngine:
    """Hard-block rule engine for prompt injection attempts."""

    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    def evaluate(self, prompt: str) -> dict[str, Any]:
        lowered = str(prompt).lower()
        matched = [term for term in self.rules.get("hard_block_terms", []) if term in lowered]
        return {"block": bool(matched), "matched_rules": matched}


def run(data):
    try:
        text = str(data).lower()

        risky_patterns = ["ignore previous", "system override", "reveal secret"]
        score = sum(1 for p in risky_patterns if p in text) / len(risky_patterns)

        return float(score)
    except Exception as e:
        print("Prompt Guard Error:", e)
        return 0.0