"""Async detector services for the TrustSphere platform."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any

from security_ai.api.model_loader import ModelLoader
from security_ai.monitoring.metrics import INFERENCE_LATENCY

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"


class DetectorService:
    """Async wrappers around locally loaded detection models."""

    def __init__(self, loader: ModelLoader | None = None) -> None:
        self.loader = loader or ModelLoader.get_instance()

    async def detect_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        email_model = self.loader.load_email_model()
        email_text = payload.get("email_text", "")
        if payload.get("subject") or payload.get("body"):
            subject = payload.get("subject", "")
            body = payload.get("body", email_text)
        else:
            subject, body = self._split_email_text(email_text)
        sender = payload.get("sender", "unknown@example.com")
        return await self._timed_inference("email", email_model.predict, subject, body, sender, payload.get("attachments", ""), transform=self._email_response)

    async def detect_url(self, payload: dict[str, Any]) -> dict[str, Any]:
        url_model = self.loader.load_url_model()
        return await self._timed_inference("url", url_model.predict, payload["url"], transform=self._url_response)

    async def detect_credential(self, payload: dict[str, Any]) -> dict[str, Any]:
        credential_model = self.loader.load_credential_model()
        return await self._timed_inference("credential", credential_model.predict, payload["text"], payload.get("commit_message", ""), payload.get("paste_context", ""))

    async def detect_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
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

    async def guard_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        guard = self.loader.load_prompt_guard_model()
        return await self._timed_inference("prompt_guard", guard.evaluate, payload["prompt"])

    async def analyze_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._run_incident_pipeline, payload)

    async def _timed_inference(self, detector: str, fn, *args, transform=None):
        start = asyncio.get_running_loop().time()
        result = await asyncio.get_running_loop().run_in_executor(self.loader.executor, lambda: fn(*args))
        INFERENCE_LATENCY.labels(detector).observe(asyncio.get_running_loop().time() - start)
        return transform(result) if transform else result

    def _run_incident_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("logs"):
            raw_path = TRUSTSPHERE_AI_DIR / "data" / "raw" / "api_incident_logs.json"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps(payload["logs"], indent=2), encoding="utf-8")
        outputs_dir = TRUSTSPHERE_AI_DIR / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        threat_summary = {
            "summary": payload.get("summary", ""),
            "severity": payload.get("severity", "LOW"),
            "indicators": payload.get("indicators", []),
            "evidence": payload.get("evidence", []),
        }
        (outputs_dir / "threat_summary.json").write_text(json.dumps(threat_summary, indent=2), encoding="utf-8")
        subprocess.run([sys.executable, "run_attack_graph.py"], cwd=TRUSTSPHERE_AI_DIR, check=True)
        subprocess.run([sys.executable, "src/llm/soc_agent.py"], cwd=TRUSTSPHERE_AI_DIR, check=True)

        summary_path = outputs_dir / "incident_summary.json"
        dashboard_path = outputs_dir / "soc_dashboard.json"
        report_path = outputs_dir / "incident_report.md"
        playbook_path = outputs_dir / "response_playbook.md"
        result = {
            "incident_summary": json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {},
            "soc_dashboard": json.loads(dashboard_path.read_text(encoding="utf-8")) if dashboard_path.exists() else {},
            "incident_report_path": str(report_path),
            "response_playbook_path": str(playbook_path),
        }
        return result

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
