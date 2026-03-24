"""Async detector services for the TrustSphere platform."""

from __future__ import annotations

import asyncio
from typing import Any

from security_ai.api.model_loader import ModelLoader
from security_ai.monitoring.metrics import INFERENCE_LATENCY


class DetectorService:
    """Async wrappers around locally loaded detection models."""

    def __init__(self, loader: ModelLoader | None = None) -> None:
        self.loader = loader or ModelLoader.get_instance()
        from security_ai.api.soc_service import SOCService

        self.soc_service = SOCService()

    async def detect_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            email_model = self.loader.load_email_model()
            email_text = payload.get("email_text", "")
            if payload.get("subject") or payload.get("body"):
                subject = payload.get("subject", "")
                body = payload.get("body", email_text)
            else:
                subject, body = self._split_email_text(email_text)
            sender = payload.get("sender", "unknown@example.com")
            return await self._timed_inference("email", email_model.predict, subject, body, sender, payload.get("attachments", ""), transform=self._email_response)
        except Exception:
            return self.soc_service.detector_result_mock("email")

    async def detect_url(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            url_model = self.loader.load_url_model()
            return await self._timed_inference("url", url_model.predict, payload["url"], transform=self._url_response)
        except Exception:
            fallback = self.soc_service.detector_result_mock("url")
            fallback["url"] = payload.get("url", fallback["url"])
            return fallback

    async def detect_credential(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            credential_model = self.loader.load_credential_model()
            return await self._timed_inference("credential", credential_model.predict, payload["text"], payload.get("commit_message", ""), payload.get("paste_context", ""))
        except Exception:
            return self.soc_service.detector_result_mock("credential")

    async def detect_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            attachment_model = self.loader.load_attachment_model()
            return await self._timed_inference(
                "attachment",
                attachment_model.predict,
                payload["filename"],
                payload["size_bytes"],
                payload.get("content_text", ""),
                payload.get("event_context", ""),
                payload.get("post_download_action", ""),
            )
        except Exception:
            return self.soc_service.detector_result_mock("attachment")

    async def guard_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            guard = self.loader.load_prompt_guard_model()
            return await self._timed_inference("prompt_guard", guard.evaluate, payload["prompt"])
        except Exception:
            return self.soc_service.detector_result_mock("prompt_guard")

    async def analyze_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            pipeline = self.loader.load_trustsphere_pipeline()
            return await self._timed_inference(
                "incident",
                pipeline.run,
                payload.get("logs", []),
                transform=lambda result: result.incident_report.model_dump(mode="json"),
            )
        except Exception:
            return self.soc_service.incident_report_mock()

    async def _timed_inference(self, detector: str, fn, *args, transform=None):
        start = asyncio.get_running_loop().time()
        result = await asyncio.get_running_loop().run_in_executor(self.loader.executor, lambda: fn(*args))
        INFERENCE_LATENCY.labels(detector).observe(asyncio.get_running_loop().time() - start)
        return transform(result) if transform else result

    def _split_email_text(self, email_text: str) -> tuple[str, str]:
        text = str(email_text or "")
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return "", ""
        return lines[0][:160], "\n".join(lines[1:]) if len(lines) > 1 else lines[0]

    def _email_response(self, result: dict[str, Any]) -> dict[str, Any]:
        probability = float(result.get("phishing_probability", 0.0))
        return {"phishing_probability": probability, "label": "phishing" if probability >= 0.5 else "safe"}

    def _url_response(self, result: dict[str, Any]) -> dict[str, Any]:
        probability = float(result.get("phishing_probability", 0.0))
        return {"phishing_probability": probability, "label": "phishing" if probability >= 0.5 else "safe", "url": result.get("url")}
