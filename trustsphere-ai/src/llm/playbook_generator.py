"""Response playbook generation for the TrustSphere offline SOC agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .prompt_templates import build_playbook_prompt
except ImportError:
    from prompt_templates import build_playbook_prompt


class PlaybookGenerator:
    """Generate structured remediation playbooks from SOC context."""

    def __init__(self, llm: Any, output_dir: str | Path) -> None:
        self.llm = llm
        self.output_dir = Path(output_dir)

    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = build_playbook_prompt(context)
        body = self.llm.generate(prompt)
        severity = str(context.get("threat_summary", {}).get("highest_severity", "LOW")).upper()
        markdown = f"# Response Playbook\n\n> Severity: **{severity}**\n\n{body.strip()}\n"
        output_path = self.output_dir / "response_playbook.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return {
            "markdown": markdown,
            "severity": severity,
            "path": output_path,
        }
