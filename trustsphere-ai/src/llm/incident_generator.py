"""Incident report generation for the TrustSphere offline SOC agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .prompt_templates import build_incident_prompt
except ImportError:
    from prompt_templates import build_incident_prompt


class IncidentReportGenerator:
    """Generate professional incident intelligence from structured SOC context."""

    def __init__(self, llm: Any, output_dir: str | Path) -> None:
        self.llm = llm
        self.output_dir = Path(output_dir)

    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = build_incident_prompt(context)
        body = self.llm.generate(prompt)
        severity = str(context.get("threat_summary", {}).get("highest_severity", "LOW")).upper()
        confidence = _extract_section_value(body, "Confidence Level")
        incident_id = f"TS-INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        markdown = (
            f"# Incident Report\n\n"
            f"> Incident ID: **{incident_id}**\n"
            f"> Generated: **{datetime.now(timezone.utc).isoformat()}**\n"
            f"> Severity: **{severity}**\n"
            f"> Confidence: **{confidence}**\n\n"
            f"{body.strip()}\n"
        )
        output_path = self.output_dir / "incident_report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return {
            "incident_id": incident_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "confidence": confidence,
            "markdown": markdown,
            "path": output_path,
        }


def _extract_section_value(markdown: str, header: str) -> str:
    lines = markdown.splitlines()
    header_lower = header.lower()
    for index, line in enumerate(lines):
        if line.strip().lower().startswith(f"## {header_lower}"):
            for next_line in lines[index + 1 :]:
                stripped = next_line.strip(" -")
                if stripped:
                    return stripped
    return "Insufficient evidence to conclude."
