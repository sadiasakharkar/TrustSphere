"""Offline SOC analyst orchestration for TrustSphere."""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

try:
    from .incident_generator import IncidentGenerator
    from .playbook_generator import PlaybookGenerator
    from .report_formatter import extract_executive_summary, save_json
except ImportError:
    from incident_generator import IncidentGenerator
    from playbook_generator import PlaybookGenerator
    from report_formatter import extract_executive_summary, save_json


LOGGER = logging.getLogger("trustsphere.soc_agent")


class LocalLLM:
    """Offline local model wrapper using Ollama first, then optional llama.cpp."""

    def __init__(
        self,
        model_name: str = "mistral:7b-instruct",
        timeout_seconds: int = 120,
        max_retries: int = 2,
        temperature: float = 0.2,
        enable_streaming: bool = True,
    ) -> None:
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.temperature = temperature
        self.enable_streaming = enable_streaming

    def generate(self, prompt: str) -> str:
        """Generate text locally with retry and timeout safeguards."""
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                return self._generate_once(prompt)
            except Exception as exc:
                last_error = exc
                LOGGER.warning("Local LLM attempt %s failed: %s", attempt, exc)
                time.sleep(min(2 * attempt, 4))
        LOGGER.warning("Falling back to deterministic mock output due to local model failure.")
        if last_error is not None:
            LOGGER.warning("Last local LLM error: %s", last_error)
        return self._mock_response(prompt)

    def _generate_once(self, prompt: str) -> str:
        if self._ollama_available():
            return self._generate_with_ollama(prompt)
        return self._generate_with_llama_cpp(prompt)

    def _generate_with_ollama(self, prompt: str) -> str:
        command = [
            "ollama",
            "run",
            self.model_name,
            prompt,
        ]
        env = os.environ.copy()
        env["OLLAMA_NUM_PREDICT"] = env.get("OLLAMA_NUM_PREDICT", "1024")
        env["OLLAMA_TEMPERATURE"] = str(self.temperature)
        result = subprocess.run(
            command,
            capture_output=not self.enable_streaming,
            text=True,
            timeout=self.timeout_seconds,
            check=True,
            env=env,
        )
        if self.enable_streaming:
            return "Local model response streamed to terminal. Review saved report artifacts."
        output = result.stdout.strip()
        if not output:
            raise RuntimeError("Ollama returned an empty response.")
        return output

    def _generate_with_llama_cpp(self, prompt: str) -> str:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("Neither Ollama nor llama-cpp-python is available locally.") from exc

        model_path = os.environ.get("TRUSTSPHERE_GGUF_PATH")
        if not model_path:
            raise RuntimeError("TRUSTSPHERE_GGUF_PATH is not set for llama.cpp inference.")

        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=max(2, os.cpu_count() or 2),
            verbose=False,
        )
        response = llm.create_completion(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=900,
            stop=["</s>"],
        )
        text = response["choices"][0]["text"].strip()
        if not text:
            raise RuntimeError("llama.cpp returned an empty response.")
        return text

    def _ollama_available(self) -> bool:
        try:
            subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            return True
        except Exception:
            return False

    def _mock_response(self, prompt: str) -> str:
        lower_prompt = prompt.lower()
        if "response playbook" in lower_prompt or "containment steps" in lower_prompt:
            return (
                "## Immediate Actions\n"
                "- Disable affected accounts.\n"
                "- Isolate impacted endpoints.\n\n"
                "## Containment Steps\n"
                "- Reset credentials and revoke active tokens.\n"
                "- Block suspicious IP ranges at perimeter controls.\n\n"
                "## Investigation Tasks\n"
                "- Review authentication logs and endpoint telemetry.\n"
                "- Validate whether privilege changes were approved.\n\n"
                "## Recovery Actions\n"
                "- Restore trusted access paths and confirm endpoint integrity.\n"
                "- Re-enable accounts after validation.\n\n"
                "## Prevention Measures\n"
                "- Enforce MFA and tighten privileged access monitoring.\n"
                "- Update detections for similar behavior.\n"
            )
        return (
            "## Executive Summary\n"
            "Suspicious authentication and post-login behavior indicate potential account compromise.\n\n"
            "## Attack Timeline\n"
            "- Suspicious access observed.\n"
            "- Follow-on anomalous activity detected.\n"
            "- Elevated risk condition confirmed.\n\n"
            "## Root Cause Analysis\n"
            "Evidence suggests misuse of credentials or an untrusted endpoint. If certainty is low, Insufficient evidence.\n\n"
            "## Impact Assessment\n"
            "Potential exposure is limited to the identified entities in the supplied context.\n\n"
            "## Confidence Level\n"
            "Medium confidence based on structured detections and rule-based correlation.\n"
        )


class TrustSphereSOCAgent:
    """Offline SOC orchestration from threat inputs to analyst-ready outputs."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2]
        self.outputs_dir = self.base_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._configure_logging()
        self.llm = LocalLLM()
        self.incident_generator = IncidentGenerator(self.llm, self.outputs_dir)
        self.playbook_generator = PlaybookGenerator(self.llm, self.outputs_dir)

    def run(self) -> dict[str, Path]:
        """Execute the full offline SOC analysis pipeline."""
        threat_summary_path, attack_paths_path = self._ensure_input_files()
        incident_markdown, context, incident_path = self.incident_generator.generate(
            threat_summary_path=threat_summary_path,
            attack_paths_path=attack_paths_path,
        )
        playbook_markdown, playbook_path = self.playbook_generator.generate(context)

        executive_summary = extract_executive_summary(
            incident_markdown=incident_markdown,
            playbook_markdown=playbook_markdown,
            metadata={
                "title": "TrustSphere Executive Incident Summary",
                "severity": context.get("risk_level", "LOW"),
                "confidence": _extract_confidence_line(incident_markdown),
                "recommended_action": _derive_recommended_action(playbook_markdown),
            },
        )
        executive_summary_path = save_json(executive_summary, self.outputs_dir / "executive_summary.json")

        self.logger.info("Incident report saved to %s", incident_path)
        self.logger.info("Response playbook saved to %s", playbook_path)
        self.logger.info("Executive summary saved to %s", executive_summary_path)
        return {
            "incident_report": incident_path,
            "response_playbook": playbook_path,
            "executive_summary": executive_summary_path,
            "log_file": self.outputs_dir / "soc_analysis.log",
        }

    def _ensure_input_files(self) -> tuple[Path, Path]:
        threat_summary_path = self.outputs_dir / "threat_summary.json"
        attack_paths_path = self.outputs_dir / "attack_paths.json"

        if not threat_summary_path.exists():
            threat_summary_path.write_text(
                json.dumps(
                    {
                        "threat_summary": "Suspicious authentication followed by privilege escalation.",
                        "risk_level": "CRITICAL",
                        "anomaly_explanations": [
                            "Impossible travel detected",
                            "Multiple failed logins",
                            "New device anomaly",
                        ],
                        "affected_entities": 3,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not attack_paths_path.exists():
            attack_paths_path.write_text(
                json.dumps(
                    {
                        "paths": [
                            {
                                "name": "credential_compromise_chain",
                                "nodes": [
                                    "phishing_email",
                                    "login_from_new_ip",
                                    "privilege_escalation",
                                    "data_exfiltration",
                                ],
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        return threat_summary_path, attack_paths_path

    def _configure_logging(self) -> logging.Logger:
        logger = logging.getLogger("trustsphere.soc_agent")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        log_path = self.outputs_dir / "soc_analysis.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(handler)
        return logger


def _extract_confidence_line(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        if "confidence" in line.lower():
            return line.strip()
    return "Insufficient evidence."


def _derive_recommended_action(playbook_markdown: str) -> str:
    for line in playbook_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped.removeprefix("- ").strip()
    return "Monitor"


if __name__ == "__main__":
    agent = TrustSphereSOCAgent()
    agent.run()
