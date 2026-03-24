"""Incident report generation for the offline TrustSphere SOC agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .prompt_templates import build_incident_prompt
    from .report_formatter import format_markdown_report
except ImportError:
    from prompt_templates import build_incident_prompt
    from report_formatter import format_markdown_report


class IncidentGenerator:
    """Generate analyst-grade incident reports from structured threat inputs."""

    def __init__(self, llm: Any, output_dir: str | Path) -> None:
        self.llm = llm
        self.output_dir = Path(output_dir)

    def generate(
        self,
        threat_summary_path: str | Path,
        attack_paths_path: str | Path,
    ) -> tuple[str, dict[str, Any], Path]:
        threat_summary = self._load_json(threat_summary_path)
        attack_paths = self._load_json(attack_paths_path)
        context = self._build_context(threat_summary, attack_paths)
        prompt = build_incident_prompt(context)
        body = self.llm.generate(prompt)
        severity = str(threat_summary.get("risk_level", "LOW")).upper()
        markdown = format_markdown_report("Incident Report", severity, body)

        output_path = self.output_dir / "incident_report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return markdown, context, output_path

    def _build_context(
        self,
        threat_summary: dict[str, Any],
        attack_paths: dict[str, Any],
    ) -> dict[str, Any]:
        compressed_paths = self._compress_attack_paths(attack_paths)
        return {
            "threat_summary": _anonymize_structure(threat_summary),
            "attack_paths_summary": compressed_paths,
            "risk_level": str(threat_summary.get("risk_level", "LOW")).upper(),
            "anomaly_explanations": threat_summary.get("anomaly_explanations", []),
        }

    def _compress_attack_paths(self, attack_paths: dict[str, Any]) -> dict[str, Any]:
        paths = attack_paths.get("paths", [])
        compressed = []
        for path in paths[:5]:
            nodes = path.get("nodes", [])
            compressed.append(
                {
                    "path_name": path.get("name", "attack_path"),
                    "node_count": len(nodes),
                    "first_step": nodes[0] if nodes else "Insufficient evidence.",
                    "last_step": nodes[-1] if nodes else "Insufficient evidence.",
                }
            )
        return {
            "path_count": len(paths),
            "compressed_paths": compressed,
        }

    def _load_json(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)


def _anonymize_structure(payload: Any) -> Any:
    if isinstance(payload, dict):
        masked: dict[str, Any] = {}
        for key, value in payload.items():
            if key in {"user", "user_id", "username", "ip_address", "ip"}:
                masked[key] = "[REDACTED]"
            else:
                masked[key] = _anonymize_structure(value)
        return masked
    if isinstance(payload, list):
        return [_anonymize_structure(item) for item in payload]
    return payload
