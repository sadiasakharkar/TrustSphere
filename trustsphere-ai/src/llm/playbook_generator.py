"""Response playbook generation for the offline TrustSphere SOC agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .prompt_templates import build_playbook_prompt
    from .report_formatter import format_markdown_report
except ImportError:
    from prompt_templates import build_playbook_prompt
    from report_formatter import format_markdown_report


class PlaybookGenerator:
    """Generate response playbooks from structured threat context."""

    def __init__(self, llm: Any, output_dir: str | Path) -> None:
        self.llm = llm
        self.output_dir = Path(output_dir)

    def generate(self, context: dict[str, Any]) -> tuple[str, Path]:
        prompt = build_playbook_prompt(context)
        body = self.llm.generate(prompt)
        severity = str(context.get("risk_level", "LOW")).upper()
        markdown = format_markdown_report("Response Playbook", severity, body)
        output_path = self.output_dir / "response_playbook.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return markdown, output_path
