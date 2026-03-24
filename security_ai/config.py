"""Configuration for TrustSphere Security AI models."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DIR = BASE_DIR / "features"
MODELS_DIR = BASE_DIR / "models"
TRAINING_DIR = BASE_DIR / "training"
EVALUATION_DIR = BASE_DIR / "evaluation"
API_DIR = BASE_DIR / "api"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_EXPORT_DIR = ARTIFACTS_DIR / "phishing_email_model"
TOKENIZER_EXPORT_DIR = ARTIFACTS_DIR / "tokenizer"
MLRUNS_DIR = ARTIFACTS_DIR / "mlruns"


@dataclass(slots=True)
class PhishingModelConfig:
    model_name_or_path: str = "microsoft/deberta-v3-base"
    max_length: int = 512
    learning_rate: float = 2e-5
    train_batch_size: int = 16
    eval_batch_size: int = 16
    num_train_epochs: int = 4
    weight_decay: float = 0.01
    random_state: int = 42
    test_size: float = 0.15
    val_size: float = 0.15
    use_local_files_only: bool = True
    fallback_model_name: str = "tfidf_logreg"
    target_metric: str = "f1"
    positive_label: int = 1

    def to_json(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path
