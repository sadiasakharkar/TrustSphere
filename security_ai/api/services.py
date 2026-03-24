"""Detector service layer for FastAPI deployment."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any

from security_ai.detect_credentials import CredentialExposurePredictor
from security_ai.predict_attachment import AttachmentPredictor
from security_ai.predict_email import EmailPredictor
from security_ai.predict_url import URLPhishingPredictor

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"


class DetectorService:
    """Async wrappers around local detector inference utilities."""

    def __init__(self) -> None:
        self.email = EmailPredictor()
        self.url = URLPhishingPredictor()
        self.credential = CredentialExposurePredictor()
        self.attachment = AttachmentPredictor()

    async def detect_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self.email.predict, payload["subject"], payload["body"], payload["sender"], payload.get("attachments", ""))

    async def detect_url(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self.url.predict, payload["url"])

    async def detect_credential(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self.credential.predict, payload["text"], payload.get("commit_message", ""), payload.get("paste_context", ""))

    async def detect_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.attachment.predict,
            payload["filename"],
            payload["size_bytes"],
            payload.get("content_text", ""),
            payload.get("event_context", ""),
            payload.get("post_download_action", ""),
        )

    async def analyze_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(_run_soc_agent, payload)


def _run_soc_agent(payload: dict[str, Any]) -> dict[str, Any]:
    outputs_dir = TRUSTSPHERE_AI_DIR / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    if payload:
        (outputs_dir / "threat_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    subprocess.run(
        [sys.executable, "src/llm/soc_agent.py"],
        cwd=TRUSTSPHERE_AI_DIR,
        check=True,
    )
    result = {
        "incident_report": outputs_dir / "incident_report.md",
        "response_playbook": outputs_dir / "response_playbook.md",
        "incident_summary": outputs_dir / "incident_summary.json",
        "soc_dashboard": outputs_dir / "soc_dashboard.json",
        "soc_log": outputs_dir / "soc_agent.log",
    }
    return {key: str(value) for key, value in result.items()}
