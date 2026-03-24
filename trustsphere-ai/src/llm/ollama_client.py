"""Offline Ollama client for TrustSphere SOC reasoning."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
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
        tags_endpoint: str = DEFAULT_OLLAMA_TAGS_URL,
        timeout_seconds: int = 120,
        max_retries: int = 2,
        temperature: float = 0.2,
        top_p: float = 0.9,
        stream: bool = False,
        production_mode: bool | None = None,
        seed: int = 42,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.tags_endpoint = tags_endpoint
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.temperature = 0.2 if temperature is None else temperature
        self.top_p = 0.9 if top_p is None else top_p
        self.stream = stream
        self.seed = seed
        env_mode = os.getenv("TRUSTSPHERE_ENV", "development").strip().lower()
        self.production_mode = production_mode if production_mode is not None else env_mode in {"prod", "production"}
        self.allow_fallback = not self.production_mode

    def health_check(self) -> dict[str, Any]:
        """Verify that Ollama is reachable and that the configured model is installed."""
        started_at = time.perf_counter()
        payload = {
            "service_reachable": False,
            "model_available": False,
            "model": self.model,
            "endpoint": self.endpoint,
            "tags_endpoint": self.tags_endpoint,
            "timeout_seconds": self.timeout_seconds,
            "production_mode": self.production_mode,
        }
        try:
            tags = self._fetch_tags()
            installed_models = [str(item.get("name", "")) for item in tags.get("models", [])]
            payload["service_reachable"] = True
            payload["installed_models"] = installed_models
            payload["model_available"] = self.model in installed_models
            payload["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
            if not payload["model_available"]:
                payload["error"] = f"Configured model '{self.model}' is not installed in Ollama."
            return payload
        except (TimeoutError, HTTPError, URLError, ConnectionError, RuntimeError, json.JSONDecodeError) as exc:
            payload["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
            payload["error"] = str(exc)
            return payload

    def generate(self, prompt: str) -> str:
        """Generate text using the local Ollama daemon with deterministic settings."""
        health = self.health_check()
        if not health["service_reachable"]:
            return self._handle_unavailable_backend(
                f"Ollama service unreachable at {self.tags_endpoint}: {health.get('error', 'unknown error')}",
                prompt,
            )
        if not health["model_available"]:
            return self._handle_unavailable_backend(
                f"Ollama model '{self.model}' is not installed.",
                prompt,
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": self.stream,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": 4096,
                "seed": self.seed,
                "repeat_penalty": 1.05,
                "num_predict": 768,
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
        message = "Ollama inference failed after retries."
        if last_error is not None:
            message = f"{message} Last Ollama error: {last_error}"
        return self._handle_unavailable_backend(message, prompt)

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

    def _fetch_tags(self) -> dict[str, Any]:
        request = Request(
            self.tags_endpoint,
            headers={"Content-Type": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError("Ollama tags endpoint is unavailable. Verify the Ollama version and service state.") from exc
            raise
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected Ollama tags payload.")
        return payload

    def _handle_unavailable_backend(self, message: str, prompt: str) -> str:
        if self.production_mode:
            raise RuntimeError(f"{message} Fallback is disabled in production mode.")
        LOGGER.warning("Falling back to deterministic local mock response. %s", INSTALL_NOTES)
        LOGGER.warning("Fallback reason: %s", message)
        return self._mock_response(prompt)

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
