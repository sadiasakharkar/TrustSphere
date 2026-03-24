"""Lazy-loading singleton for TrustSphere model inference components."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
from typing import Any

from security_ai.detect_credentials import CredentialExposurePredictor
from security_ai.predict_attachment import AttachmentPredictor
from security_ai.predict_email import EmailPredictor
from security_ai.predict_url import URLPhishingPredictor
from security_ai.prompt_guard import PromptInjectionGuard


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

    def load_email_model(self) -> EmailPredictor:
        return self._get_or_create("email", EmailPredictor)

    def load_url_model(self) -> URLPhishingPredictor:
        return self._get_or_create("url", URLPhishingPredictor)

    def load_credential_model(self) -> CredentialExposurePredictor:
        return self._get_or_create("credential", CredentialExposurePredictor)

    def load_attachment_model(self) -> AttachmentPredictor:
        return self._get_or_create("attachment", AttachmentPredictor)

    def load_prompt_guard_model(self) -> PromptInjectionGuard:
        return self._get_or_create("prompt_guard", PromptInjectionGuard)

    def load_anomaly_model(self) -> dict[str, Any]:
        return self._get_or_create("ueba_anomaly", lambda: {"status": "available", "source": str(Path('trustsphere-ai/saved_models'))})

    def load_risk_engine(self) -> dict[str, Any]:
        return self._get_or_create("risk_engine", lambda: {"status": "available"})

    def load_attack_graph_engine(self) -> dict[str, Any]:
        return self._get_or_create("attack_graph", lambda: {"status": "available"})

    def load_soc_analyst(self) -> dict[str, Any]:
        return self._get_or_create("soc_analyst", lambda: {"status": "available"})

    def warmup(self) -> None:
        self.load_email_model()
        self.load_url_model()
        self.load_credential_model()
        self.load_attachment_model()
        self.load_prompt_guard_model()

    def _get_or_create(self, key: str, factory) -> Any:
        with self._lock:
            if key not in self._models:
                self._models[key] = factory()
            return self._models[key]
