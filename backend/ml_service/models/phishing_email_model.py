"""Model wrappers for phishing email detection."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

LOGGER = logging.getLogger(__name__)

try:
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoModelForSequenceClassification = None
    AutoTokenizer = None
    DataCollatorWithPadding = None
    Trainer = None
    TrainingArguments = None


@dataclass(slots=True)
class ModelBundle:
    model: Any
    tokenizer: Any | None
    model_type: str
    metadata: dict[str, Any]


class ClassicalPhishingModel:
    """Deterministic fallback model used when transformers are unavailable."""

    def __init__(self) -> None:
        self.pipeline = Pipeline(
            steps=[
                (
                    "features",
                    ColumnTransformer(
                        transformers=[
                            ("text", TfidfVectorizer(max_features=3000, ngram_range=(1, 2)), "combined_text"),
                            (
                                "meta",
                                Pipeline(steps=[("scale", StandardScaler(with_mean=False))]),
                                [
                                    "urgency_keyword_count",
                                    "financial_term_count",
                                    "impersonation_signal_count",
                                    "sender_domain_entropy",
                                    "link_mismatch_score",
                                    "attachment_presence",
                                    "url_count",
                                    "body_length",
                                    "exclamation_ratio",
                                ],
                            ),
                        ]
                    ),
                ),
                ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")),
            ]
        )

    def fit(self, train_df, train_labels) -> None:
        self.pipeline.fit(train_df, train_labels)

    def predict_proba(self, eval_df) -> np.ndarray:
        return self.pipeline.predict_proba(eval_df)

    def save(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path / "model.joblib")
        return path / "model.joblib"


class TransformerPhishingModel:
    """Transformer training wrapper for DeBERTa phishing detection."""

    def __init__(self, model_name_or_path: str, local_files_only: bool = True) -> None:
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers/torch are not installed in this environment.")
        self.model_name_or_path = model_name_or_path
        self.local_files_only = local_files_only
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, local_files_only=local_files_only)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path, num_labels=2, local_files_only=local_files_only)

    def save(self, model_dir: str | Path, tokenizer_dir: str | Path, config: dict[str, Any]) -> None:
        model_path = Path(model_dir)
        tokenizer_path = Path(tokenizer_dir)
        model_path.mkdir(parents=True, exist_ok=True)
        tokenizer_path.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(tokenizer_path)
        (model_path / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")



def run(data):
    try:
        text = str(data).lower()

        phishing_words = ["urgent", "click", "verify", "bank", "login"]
        score = sum(1 for w in phishing_words if w in text) / len(phishing_words)

        return float(score)
    except Exception as e:
        print("Phishing Error:", e)
        return 0.0