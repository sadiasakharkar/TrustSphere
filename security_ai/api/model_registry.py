"""MLflow-aware model registry helpers for Security AI services."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except Exception:
    mlflow = None
    MLFLOW_AVAILABLE = False


class ModelRegistry:
    """Registry facade that uses MLflow when available and local manifests otherwise."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / "artifacts"
        self.registry_manifest = self.artifacts_dir / "model_registry.json"

    def register_model(self, model_name: str, metadata: dict[str, Any]) -> None:
        payload = self._load_manifest()
        payload[model_name] = metadata
        self.registry_manifest.parent.mkdir(parents=True, exist_ok=True)
        self.registry_manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if MLFLOW_AVAILABLE:
            try:
                mlflow.set_tracking_uri((self.artifacts_dir / "mlruns").as_uri())
                with mlflow.start_run(run_name=f"register_{model_name}"):
                    mlflow.log_params({"model_name": model_name, **{key: str(value) for key, value in metadata.items()}})
            except Exception as exc:
                LOGGER.warning("MLflow registration failed for %s: %s", model_name, exc)

    def get_model_metadata(self, model_name: str) -> dict[str, Any]:
        return self._load_manifest().get(model_name, {})

    def _load_manifest(self) -> dict[str, Any]:
        if self.registry_manifest.exists():
            return json.loads(self.registry_manifest.read_text(encoding="utf-8"))
        return {}
