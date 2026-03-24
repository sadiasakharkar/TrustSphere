"""Artifact persistence for the offline TrustSphere training pipeline."""

from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import joblib


LOGGER = logging.getLogger(__name__)


def save_artifacts(
    final_model: Any,
    scaler_bundle: dict[str, Any],
    feature_columns: list[str],
    metadata: dict[str, Any],
    artifact_dir: str | Path,
) -> dict[str, Path]:
    """Persist model, scaler, feature columns, and metadata."""
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / "final_model.pkl"
    scaler_path = artifact_dir / "scaler.pkl"
    feature_columns_path = artifact_dir / "feature_columns.json"
    metadata_path = artifact_dir / "model_metadata.json"

    joblib.dump(final_model, model_path)
    joblib.dump(scaler_bundle, scaler_path)

    with feature_columns_path.open("w", encoding="utf-8") as handle:
        json.dump(feature_columns, handle, indent=2)

    enriched_metadata = {
        **metadata,
        "saved_at": datetime.utcnow().isoformat(),
        "feature_count": len(feature_columns),
    }
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(enriched_metadata, handle, indent=2)

    LOGGER.info("Artifacts saved under %s", artifact_dir)
    return {
        "final_model": model_path,
        "scaler": scaler_path,
        "feature_columns": feature_columns_path,
        "metadata": metadata_path,
    }
