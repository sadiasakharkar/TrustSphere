"""SOC-grade prompt templates for TrustSphere offline LLM reasoning."""

from __future__ import annotations

import json
from typing import Any

GUARDRAILS = (
    "You are a senior SOC analyst at a global bank. "
    "Analyze only the supplied evidence. "
    "Do not hallucinate. "
    "If evidence is insufficient, say exactly: Insufficient evidence to conclude. "
    "Use concise, professional enterprise SOC language."
)


def build_incident_prompt(context: dict[str, Any]) -> str:
    return (
        f"{GUARDRAILS}\n\n"
        "Produce a markdown incident analysis with these exact sections:\n"
        "1. Executive Summary\n"
        "2. Attack Timeline\n"
        "3. Root Cause Analysis\n"
        "4. Impact Assessment\n"
        "5. MITRE ATT&CK Mapping\n"
        "6. Confidence Level\n"
        "7. Recommended Actions\n\n"
        "Rules:\n"
        "- Stay evidence-based and non-speculative.\n"
        "- Mention specific MITRE stages only if present in context.\n"
        "- If evidence is incomplete, state: Insufficient evidence to conclude.\n"
        "- Keep the response compact and analyst-ready.\n\n"
        f"Context:\n{json.dumps(context, indent=2)}"
    )


def build_playbook_prompt(context: dict[str, Any]) -> str:
    return (
        f"{GUARDRAILS}\n\n"
        "Produce a markdown SOC response playbook with these exact sections:\n"
        "1. Immediate Containment\n"
        "2. Investigation Steps\n"
        "3. Remediation Actions\n"
        "4. Prevention Measures\n"
        "5. Monitoring Recommendations\n\n"
        "Rules:\n"
        "- Prioritize banking-safe containment and evidence preservation.\n"
        "- Do not invent infrastructure not shown in the context.\n"
        "- If evidence is incomplete, state: Insufficient evidence to conclude.\n"
        "- Keep actions operational and sequenced.\n\n"
        f"Context:\n{json.dumps(context, indent=2)}"
    )
