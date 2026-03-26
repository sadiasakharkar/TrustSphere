"""Credential exposure detector models and inference helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support

LOGGER = logging.getLogger(__name__)

try:
    import spacy
    from spacy.tokens import DocBin
    SPACY_AVAILABLE = True
except Exception:
    spacy = None
    DocBin = None
    SPACY_AVAILABLE = False


@dataclass(slots=True)
class CredentialModelBundle:
    classifier: Any
    metadata: dict[str, Any]
    ner_ready: bool


class RegexContextCredentialDetector:
    """Primary local model for credential exposure scoring."""

    def __init__(self, random_state: int = 42) -> None:
        self.classifier = RandomForestClassifier(n_estimators=200, random_state=random_state, class_weight="balanced")

    def fit(self, x_train, y_train) -> None:
        self.classifier.fit(x_train, y_train)

    def predict_proba(self, x_values) -> np.ndarray:
        return self.classifier.predict_proba(x_values)

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.classifier, path)
        return path


class SpacyCredentialTrainer:
    """Optional spaCy transformer NER trainer for credential entities."""

    def __init__(self, model_name: str = "en_core_web_trf") -> None:
        self.model_name = model_name

    def train(self, training_examples: list[tuple[str, dict[str, Any]]], output_dir: str | Path) -> dict[str, Any]:
        if not SPACY_AVAILABLE:
            raise RuntimeError("spaCy is not installed in this environment.")
        nlp = spacy.blank("en")
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        for label in ["CREDENTIAL", "SECRET", "TOKEN"]:
            ner.add_label(label)
        optimizer = nlp.begin_training()
        for _ in range(10):
            losses = {}
            for text, annotations in training_examples:
                example = spacy.training.Example.from_dict(nlp.make_doc(text), annotations)
                nlp.update([example], sgd=optimizer, losses=losses)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(output_path)
        return {"ner_model_path": str(output_path), "entity_labels": ["CREDENTIAL", "SECRET", "TOKEN"]}


def classification_report(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    predicted = (probabilities >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predicted, average="binary", zero_division=0)
    return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}


def run(data):
    try:
        # simple heuristic
        text = str(data).lower()

        keywords = ["password", "otp", "secret", "token", "api_key"]
        score = sum(1 for k in keywords if k in text) / len(keywords)

        return float(score)
    except Exception as e:
        print("Credential Error:", e)
        return 0.0