"""Offline Ollama client for TrustSphere SOC reasoning."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "mistral:7b-instruct"
INSTALL_NOTES = (
    "Install Ollama locally and pull a compatible model before running:\n"
    "  1. Install Ollama for your OS.\n"
    "  2. Start the local service.\n"
    "  3. Run: ollama pull mistral:7b-instruct\n"
    "  4. Verify with: ollama run mistral:7b-instruct"
)


class LocalLLM:
    """Deterministic offline wrapper around the Ollama local HTTP API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        endpoint: str = DEFAULT_OLLAMA_URL,
        timeout_seconds: int = 120,
        max_retries: int = 2,
        temperature: float = 0.2,
        top_p: float = 0.9,
        stream: bool = False,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.temperature = temperature
        self.top_p = top_p
        self.stream = stream

    def generate(self, prompt: str) -> str:
        """Generate text using the local Ollama daemon, with offline-safe fallback."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": self.stream,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": 4096,
            },
        }
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                return self._post_generate(payload)
            except (TimeoutError, HTTPError, URLError, ConnectionError, RuntimeError, json.JSONDecodeError) as exc:
                last_error = exc
                LOGGER.warning("Ollama generation attempt %s failed: %s", attempt, exc)
                time.sleep(min(2 * attempt, 4))
        LOGGER.warning("Falling back to deterministic local mock response. %s", INSTALL_NOTES)
        if last_error is not None:
            LOGGER.warning("Last Ollama error: %s", last_error)
        return self._mock_response(prompt)

    def _post_generate(self, payload: dict[str, Any]) -> str:
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        if self.stream:
            chunks = [json.loads(line) for line in raw.splitlines() if line.strip()]
            text = "".join(chunk.get("response", "") for chunk in chunks)
        else:
            text = json.loads(raw).get("response", "")
        text = text.strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response.")
        return text

    def _mock_response(self, prompt: str) -> str:
        lower_prompt = prompt.lower()
        if "playbook" in lower_prompt:
            return (
                "## Immediate Containment\n"
                "- Disable affected accounts and revoke active sessions.\n"
                "- Isolate implicated hosts from the banking network.\n\n"
                "## Investigation Steps\n"
                "- Validate authentication history, privilege changes, and data access logs.\n"
                "- Confirm whether the observed host and IP pivots are authorized.\n\n"
                "## Remediation Actions\n"
                "- Reset credentials, rotate privileged secrets, and remove unauthorized access.\n"
                "- Reimage or remediate impacted endpoints if compromise is confirmed.\n\n"
                "## Prevention Measures\n"
                "- Enforce MFA and tighten privileged access governance.\n"
                "- Add detections for repeated pivoting, privilege change, and exfiltration patterns.\n\n"
                "## Monitoring Recommendations\n"
                "- Monitor for recurrence of the same user, host, and MITRE stages for 72 hours."
            )
        return (
            "## Executive Summary\n"
            "Suspicious authentication followed by privileged activity indicates probable credential compromise.\n\n"
            "## Attack Timeline\n"
            "- Initial suspicious access observed from an anomalous source.\n"
            "- Privileged actions and host pivots followed in sequence.\n"
            "- Data access or exfiltration activity raised the incident severity.\n\n"
            "## Root Cause Analysis\n"
            "The most likely cause is misuse of valid credentials. If forensic evidence is incomplete, state: Insufficient evidence to conclude.\n\n"
            "## Impact Assessment\n"
            "Privileged access and sensitive systems may have been exposed within the affected attack chain.\n\n"
            "## MITRE ATT&CK Mapping\n"
            "Observed behavior aligns with Initial Access, Privilege Escalation, Lateral Movement, and Exfiltration stages.\n\n"
            "## Confidence Level\n"
            "High confidence based on correlated UEBA anomalies and attack graph continuity.\n\n"
            "## Recommended Actions\n"
            "Immediately contain the account and hosts, preserve evidence, and initiate SOC investigation."
        )


def write_install_notes(output_path: str | Path) -> Path:
    """Persist Ollama setup notes for offline operators."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(INSTALL_NOTES + "\n", encoding="utf-8")
    return destination
