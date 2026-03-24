"""Formatting helpers for TrustSphere SOC outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def severity_banner(severity: str) -> str:
    """Return a markdown severity banner."""
    normalized = str(severity or "LOW").upper()
    return f"> Severity: **{normalized}**"


def format_markdown_report(title: str, severity: str, body: str) -> str:
    """Wrap a body in a consistent markdown report format."""
    return f"# {title}\n\n{severity_banner(severity)}\n\n{body.strip()}\n"


def extract_executive_summary(
    incident_markdown: str,
    playbook_markdown: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Create a compact JSON summary for executive dashboards."""
    return {
        "title": metadata.get("title", "TrustSphere Incident Intelligence"),
        "severity": metadata.get("severity", "LOW"),
        "incident_excerpt": _first_nonempty_section_line(incident_markdown),
        "playbook_excerpt": _first_nonempty_section_line(playbook_markdown),
        "confidence": metadata.get("confidence", "Insufficient evidence."),
        "recommended_action": metadata.get("recommended_action", "Monitor"),
    }


def save_json(data: dict[str, Any], output_path: str | Path) -> Path:
    """Persist a JSON document."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return output_path


def _first_nonempty_section_line(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            return stripped
    return "Insufficient evidence."
