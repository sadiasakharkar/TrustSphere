"""MLflow-backed registry helpers for TrustSphere model serving."""

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


class MLflowRegistry:
    """Registry facade with offline manifest fallback."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / "artifacts"
        self.manifest_path = self.artifacts_dir / "model_registry.json"
        self.mlruns_path = self.artifacts_dir / "mlruns"

    def register_model(self, model_name: str, metadata: dict[str, Any]) -> None:
        manifest = self._load_manifest()
        manifest[model_name] = metadata
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if MLFLOW_AVAILABLE:
            try:
                mlflow.set_tracking_uri(self.mlruns_path.as_uri())
                with mlflow.start_run(run_name=f"register_{model_name}"):
                    for key, value in metadata.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(key, value)
                        else:
                            mlflow.log_param(key, str(value))
            except Exception as exc:
                LOGGER.warning("MLflow registration failed for %s: %s", model_name, exc)

    def load_latest_production_model(self, model_name: str) -> dict[str, Any]:
        return self._load_manifest().get(model_name, {})

    def _load_manifest(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {}
