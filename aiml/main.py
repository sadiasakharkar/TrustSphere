"""Offline end-to-end TrustSphere AIML pipeline."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from features.feature_engineering import extract_behavioral_features
from models.train_model import train_and_select_model
from pipeline.save_artifacts import save_artifacts
from preprocessing.normalize_logs import normalize_logs
from preprocessing.scaler_pipeline import fit_scaler, transform_data
from simulator.log_generator import generate_logs


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
RAW_LOG_PATH = BASE_DIR / "data" / "raw" / "logs.csv"
NORMALIZED_PATH = BASE_DIR / "data" / "processed" / "normalized_logs.csv"
FEATURES_PATH = BASE_DIR / "data" / "processed" / "features.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def main() -> None:
    """Run the complete offline AIML pipeline end to end."""
    LOGGER.info("Starting offline TrustSphere AIML pipeline")

    generate_logs(output_path=RAW_LOG_PATH)
    normalize_logs(RAW_LOG_PATH, NORMALIZED_PATH)

    feature_frame, _ = extract_behavioral_features(NORMALIZED_PATH, FEATURES_PATH)
    feature_columns = feature_frame.select_dtypes(include=["number", "bool"]).columns.tolist()
    feature_columns = [
        column
        for column in feature_columns
        if column not in {"login_success", "timestamp_unix", "is_anomaly"}
    ]

    scaler_artifact_path = ARTIFACTS_DIR / "scaler.pkl"
    scaler, scaler_columns = fit_scaler(feature_frame[feature_columns], scaler_type="robust", artifact_path=scaler_artifact_path)
    scaled_features = transform_data(feature_frame[feature_columns], scaler, scaler_columns)

    training_input = feature_frame.copy()
    training_input[scaler_columns] = scaled_features[scaler_columns]
    training_result = train_and_select_model(training_input, scaler_columns, ARTIFACTS_DIR)

    save_artifacts(
        final_model=training_result.selected_model,
        scaler_bundle={"scaler": scaler, "columns": scaler_columns, "scaler_type": "robust"},
        feature_columns=scaler_columns,
        metadata=training_result.metadata,
        artifact_dir=ARTIFACTS_DIR,
    )

    LOGGER.info(
        "Pipeline complete | model=%s | rows=%s",
        training_result.selected_model_name,
        len(training_result.scored_frame),
    )


if __name__ == "__main__":
    main()
