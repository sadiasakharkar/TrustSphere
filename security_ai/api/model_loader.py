"""Lazy-loading singleton for TrustSphere model inference components."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
import sys
from typing import Any
from security_ai.api.ml_runtime.safe_import import ML_AVAILABLE

BASE_DIR = Path(__file__).resolve().parents[2]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"
if str(TRUSTSPHERE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(TRUSTSPHERE_AI_DIR))


class ModelLoader:
    """Singleton registry that loads local models once and caches them in memory."""

    _instance: "ModelLoader | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._models: dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=8)

    @classmethod
    def get_instance(cls) -> "ModelLoader":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load_email_model(self):
        if not ML_AVAILABLE:
            raise RuntimeError("ML runtime disabled")
        return self._get_or_create("email", lambda: __import__("security_ai.predict_email", fromlist=["EmailPredictor"]).EmailPredictor())

    def load_url_model(self):
        if not ML_AVAILABLE:
            raise RuntimeError("ML runtime disabled")
        return self._get_or_create("url", lambda: __import__("security_ai.predict_url", fromlist=["URLPhishingPredictor"]).URLPhishingPredictor())

    def load_credential_model(self):
        if not ML_AVAILABLE:
            raise RuntimeError("ML runtime disabled")
        return self._get_or_create("credential", lambda: __import__("security_ai.detect_credentials", fromlist=["CredentialExposurePredictor"]).CredentialExposurePredictor())

    def load_attachment_model(self):
        if not ML_AVAILABLE:
            raise RuntimeError("ML runtime disabled")
        return self._get_or_create("attachment", lambda: __import__("security_ai.predict_attachment", fromlist=["AttachmentPredictor"]).AttachmentPredictor())

    def load_prompt_guard_model(self):
        if not ML_AVAILABLE:
            raise RuntimeError("ML runtime disabled")
        return self._get_or_create("prompt_guard", lambda: __import__("security_ai.prompt_guard", fromlist=["PromptInjectionGuard"]).PromptInjectionGuard())

    def load_anomaly_model(self) -> dict[str, Any]:
        return self._get_or_create("ueba_anomaly", lambda: {"status": "available", "source": str(Path('trustsphere-ai/saved_models'))})

    def load_risk_engine(self) -> dict[str, Any]:
        return self._get_or_create("risk_engine", lambda: {"status": "available"})

    def load_attack_graph_engine(self) -> dict[str, Any]:
        return self._get_or_create("attack_graph", lambda: {"status": "available"})

    def load_soc_analyst(self) -> dict[str, Any]:
        return self._get_or_create("soc_analyst", lambda: {"status": "available"})

    def load_trustsphere_pipeline(self):
        def factory():
            from src.pipeline.unified_intelligence_pipeline import UnifiedIntelligencePipeline

            return UnifiedIntelligencePipeline(TRUSTSPHERE_AI_DIR)

        return self._get_or_create("trustsphere_pipeline", factory)

    def warmup(self) -> None:
        for loader in [
            self.load_email_model,
            self.load_url_model,
            self.load_credential_model,
            self.load_attachment_model,
            self.load_prompt_guard_model,
        ]:
            try:
                loader()
            except Exception:
                continue

    def _get_or_create(self, key: str, factory) -> Any:
        with self._lock:
            if key not in self._models:
                self._models[key] = factory()
            return self._models[key]
