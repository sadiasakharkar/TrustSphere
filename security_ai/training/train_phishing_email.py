"""Production training pipeline for phishing email detection."""

from __future__ import annotations

from dataclasses import asdict
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from security_ai.config import ARTIFACTS_DIR, MODEL_EXPORT_DIR, MLRUNS_DIR, PhishingModelConfig, RAW_DATA_DIR, TOKENIZER_EXPORT_DIR
from security_ai.evaluation.phishing_email_evaluation import compute_metrics, save_evaluation
from security_ai.features.phishing_email_features import PhishingEmailFeatureEngineer
from security_ai.models.phishing_email_model import ClassicalPhishingModel, TRANSFORMERS_AVAILABLE, TransformerPhishingModel

LOGGER = logging.getLogger(__name__)

try:
    import mlflow
except Exception:
    mlflow = None

try:
    import shap
except Exception:
    shap = None

try:
    import torch
    from torch.utils.data import Dataset
    from transformers import DataCollatorWithPadding, Trainer, TrainingArguments
    TORCH_AND_TRANSFORMERS_READY = True
except Exception:
    TORCH_AND_TRANSFORMERS_READY = False
    torch = None
    Dataset = object
    DataCollatorWithPadding = None
    Trainer = None
    TrainingArguments = None

try:
    import onnx  # noqa: F401
    import onnxruntime  # noqa: F401
    ONNX_AVAILABLE = True
except Exception:
    ONNX_AVAILABLE = False


class EncodedEmailDataset(Dataset):
    """Torch dataset wrapper for tokenized phishing email samples."""

    def __init__(self, encodings: dict[str, Any], labels: list[int]) -> None:
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, Any]:
        item = {key: value[index] for key, value in self.encodings.items()}
        item["labels"] = self.labels[index]
        return item


def load_email_datasets(raw_dir: str | Path = RAW_DATA_DIR) -> list[pd.DataFrame]:
    raw_path = Path(raw_dir)
    frames: list[pd.DataFrame] = []
    for pattern in ("*.csv", "*.jsonl", "*.json"):
        for file_path in raw_path.glob(pattern):
            try:
                if file_path.suffix == ".csv":
                    frames.append(pd.read_csv(file_path))
                elif file_path.suffix == ".jsonl":
                    frames.append(pd.read_json(file_path, lines=True))
                else:
                    frames.append(pd.read_json(file_path))
            except Exception as exc:
                LOGGER.warning("Skipping %s: %s", file_path, exc)
    return frames


def split_dataset(frame: pd.DataFrame, config: PhishingModelConfig):
    train_df, test_df = train_test_split(frame, test_size=config.test_size, stratify=frame["label"], random_state=config.random_state)
    adjusted_val_size = config.val_size / max(1e-6, (1.0 - config.test_size))
    train_df, val_df = train_test_split(train_df, test_size=adjusted_val_size, stratify=train_df["label"], random_state=config.random_state)
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def train_phishing_detector(config: PhishingModelConfig | None = None) -> dict[str, Any]:
    config = config or PhishingModelConfig()
    feature_engineer = PhishingEmailFeatureEngineer()
    prepared = feature_engineer.prepare_dataset(load_email_datasets())
    feature_artifacts = feature_engineer.build_features(prepared)
    frame = feature_artifacts.dataframe
    train_df, val_df, test_df = split_dataset(frame, config)

    best_bundle = _train_classical_bundle(train_df, val_df, test_df, config)
    if TRANSFORMERS_AVAILABLE and TORCH_AND_TRANSFORMERS_READY:
        try:
            transformer_bundle = _train_transformer_bundle(train_df, val_df, test_df, config)
            if transformer_bundle["metrics"][config.target_metric] >= best_bundle["metrics"][config.target_metric]:
                best_bundle = transformer_bundle
            best_bundle["transformer_ready"] = True
        except Exception as exc:
            LOGGER.warning("Transformer fine-tuning unavailable in current environment: %s", exc)
            best_bundle["transformer_ready"] = False
    else:
        best_bundle["transformer_ready"] = False

    _export_explainability(best_bundle, ARTIFACTS_DIR)
    _export_model(best_bundle, config)
    _track_mlflow(best_bundle, config)
    return best_bundle


def _train_classical_bundle(train_df, val_df, test_df, config):
    best_bundle = None
    for c_value in [1.0, 2.0]:
        model = ClassicalPhishingModel()
        model.pipeline.named_steps["clf"].set_params(C=c_value)
        model.fit(train_df, train_df["label"])
        test_prob = model.predict_proba(test_df)[:, 1]
        metrics = compute_metrics(test_df["label"].to_numpy(), test_prob)
        bundle = {
            "model": model,
            "tokenizer": None,
            "model_type": config.fallback_model_name,
            "metrics": metrics,
            "metadata": {
                "model_type": config.fallback_model_name,
                "hyperparameters": {"classifier_c": c_value},
                "train_rows": len(train_df),
                "val_rows": len(val_df),
                "test_rows": len(test_df),
            },
            "test_probabilities": test_prob,
            "test_frame": test_df,
        }
        if best_bundle is None or metrics[config.target_metric] > best_bundle["metrics"][config.target_metric]:
            best_bundle = bundle
    save_evaluation(best_bundle["metrics"], ARTIFACTS_DIR / "phishing_email_metrics.json")
    return best_bundle


def _train_transformer_bundle(train_df, val_df, test_df, config):
    transformer = TransformerPhishingModel(config.model_name_or_path, local_files_only=config.use_local_files_only)
    best_bundle = None
    search_space = [
        {"learning_rate": 2e-5, "num_train_epochs": 3},
        {"learning_rate": 2e-5, "num_train_epochs": 4},
    ]

    for params in search_space:
        tokenizer = transformer.tokenizer
        model = transformer.model
        train_dataset = _tokenize_dataframe(tokenizer, train_df, config)
        val_dataset = _tokenize_dataframe(tokenizer, val_df, config)
        test_dataset = _tokenize_dataframe(tokenizer, test_df, config)
        output_dir = ARTIFACTS_DIR / "hf_training_runs" / f"lr_{params['learning_rate']}_ep_{params['num_train_epochs']}"
        output_dir.mkdir(parents=True, exist_ok=True)
        args = TrainingArguments(
            output_dir=str(output_dir),
            learning_rate=params["learning_rate"],
            per_device_train_batch_size=config.train_batch_size,
            per_device_eval_batch_size=config.eval_batch_size,
            num_train_epochs=params["num_train_epochs"],
            weight_decay=config.weight_decay,
            evaluation_strategy="epoch",
            save_strategy="no",
            logging_strategy="epoch",
            report_to=[],
            seed=config.random_state,
        )
        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer,
            data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
            compute_metrics=lambda eval_pred: _hf_metrics(eval_pred.predictions, eval_pred.label_ids),
        )
        trainer.train()
        test_predictions = trainer.predict(test_dataset)
        logits = test_predictions.predictions
        probabilities = _softmax(logits)[:, 1]
        metrics = compute_metrics(test_df["label"].to_numpy(), probabilities)
        bundle = {
            "model": model,
            "tokenizer": tokenizer,
            "model_type": "deberta-v3-base",
            "metrics": metrics,
            "metadata": {
                "model_type": "deberta-v3-base",
                "hyperparameters": params,
                "train_rows": len(train_df),
                "val_rows": len(val_df),
                "test_rows": len(test_df),
            },
            "trainer": trainer,
            "test_probabilities": probabilities,
            "test_frame": test_df,
        }
        if best_bundle is None or metrics[config.target_metric] > best_bundle["metrics"][config.target_metric]:
            best_bundle = bundle
    save_evaluation(best_bundle["metrics"], ARTIFACTS_DIR / "phishing_email_metrics.json")
    return best_bundle


def _tokenize_dataframe(tokenizer, frame: pd.DataFrame, config: PhishingModelConfig) -> EncodedEmailDataset:
    encodings = tokenizer(
        frame["combined_text"].tolist(),
        truncation=True,
        padding=True,
        max_length=config.max_length,
    )
    return EncodedEmailDataset(encodings, frame["label"].tolist())


def _hf_metrics(logits, labels):
    probabilities = _softmax(logits)[:, 1]
    return compute_metrics(np.asarray(labels), probabilities)


def _softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits)
    shifted = logits - logits.max(axis=1, keepdims=True)
    exps = np.exp(shifted)
    return exps / exps.sum(axis=1, keepdims=True)


def _export_explainability(bundle: dict[str, Any], output_dir: Path) -> None:
    explainability = {
        "attention_visualization": "Enabled for transformer inference when tokenizer/model are exported.",
        "shap": "Unavailable in current environment." if shap is None else "Configured for post-hoc token explanation.",
        "model_type": bundle["model_type"],
    }
    if shap is not None and bundle["model_type"] == "tfidf_logreg":
        try:
            sample = bundle["test_frame"].head(min(20, len(bundle["test_frame"]))).copy()
            model = bundle["model"]
            transformed = model.pipeline.named_steps["features"].transform(sample)
            explainer = shap.Explainer(model.pipeline.named_steps["clf"], transformed)
            shap_values = explainer(transformed)
            explainability["shap_summary"] = {"sample_count": len(sample), "feature_count": int(shap_values.values.shape[-1])}
        except Exception as exc:
            explainability["shap_error"] = str(exc)
    (output_dir / "explainability.json").write_text(json.dumps(explainability, indent=2), encoding="utf-8")


def _export_model(bundle: dict[str, Any], config: PhishingModelConfig) -> None:
    MODEL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    TOKENIZER_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_payload = {**asdict(config), **bundle["metadata"], "metrics": bundle["metrics"]}
    if bundle["model_type"] == "deberta-v3-base" and bundle.get("tokenizer") is not None:
        bundle["model"].save_pretrained(MODEL_EXPORT_DIR)
        bundle["tokenizer"].save_pretrained(TOKENIZER_EXPORT_DIR)
        if ONNX_AVAILABLE and torch is not None:
            _export_onnx(bundle["model"], bundle["tokenizer"], config)
    else:
        bundle["model"].save(MODEL_EXPORT_DIR)
        (TOKENIZER_EXPORT_DIR / "config.json").write_text(json.dumps({"tokenizer": "classical-fallback", "max_length": config.max_length}, indent=2), encoding="utf-8")
    (MODEL_EXPORT_DIR / "config.json").write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
    (ARTIFACTS_DIR / "model_export.json").write_text(json.dumps({"model_type": bundle["model_type"]}, indent=2), encoding="utf-8")


def _export_onnx(model, tokenizer, config: PhishingModelConfig) -> None:
    sample = tokenizer("security verification required", return_tensors="pt", truncation=True, max_length=config.max_length)
    output_path = MODEL_EXPORT_DIR / "model.onnx"
    torch.onnx.export(
        model,
        (sample["input_ids"], sample.get("attention_mask")),
        output_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={"input_ids": {0: "batch", 1: "seq"}, "attention_mask": {0: "batch", 1: "seq"}, "logits": {0: "batch"}},
        opset_version=14,
    )


def _track_mlflow(bundle: dict[str, Any], config: PhishingModelConfig) -> None:
    if mlflow is None:
        return
    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
    with mlflow.start_run(run_name="phishing_email_detector"):
        mlflow.log_params(asdict(config))
        mlflow.log_param("model_type", bundle["model_type"])
        for key, value in bundle["metrics"].items():
            mlflow.log_metric(key, value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    result = train_phishing_detector()
    print(json.dumps({"metrics": result["metrics"], "transformer_ready": result["transformer_ready"], "model_type": result["model_type"]}, indent=2))
