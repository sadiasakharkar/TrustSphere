"""Structured export helpers for TrustSphere SOC outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReportExporter:
    """Export LLM outputs for markdown and frontend dashboard consumption."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, incident: dict[str, Any], playbook: dict[str, Any], context: dict[str, Any]) -> dict[str, Path]:
        summary = {
            "incident_id": incident.get("incident_id"),
            "timestamp": incident.get("timestamp"),
            "severity": incident.get("severity"),
            "confidence": incident.get("confidence"),
            "affected_users": context.get("affected_users", []),
            "mitre_stages": context.get("mitre_stages", []),
            "key_evidence": context.get("key_evidence", [])[:8],
            "recommended_action": self._first_bullet(playbook.get("markdown", "")),
        }
        dashboard = {
            "incident": summary,
            "threat_summary": context.get("threat_summary", {}),
            "timeline": context.get("attack_timeline", [])[:10],
            "playbook_excerpt": self._extract_section_excerpt(playbook.get("markdown", "")),
        }
        summary_path = self._write_json(summary, self.output_dir / "incident_summary.json")
        dashboard_path = self._write_json(dashboard, self.output_dir / "soc_dashboard.json")
        return {
            "incident_report": incident["path"],
            "response_playbook": playbook["path"],
            "incident_summary": summary_path,
            "soc_dashboard": dashboard_path,
        }

    def _write_json(self, payload: dict[str, Any], path: Path) -> Path:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def _first_bullet(self, markdown: str) -> str:
        for line in markdown.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                return stripped.lstrip("- ")
        return "Insufficient evidence to conclude."

    def _extract_section_excerpt(self, markdown: str) -> str:
        lines = [line.strip() for line in markdown.splitlines() if line.strip() and not line.startswith("#") and not line.startswith(">")]
        return lines[0] if lines else "Insufficient evidence to conclude."
