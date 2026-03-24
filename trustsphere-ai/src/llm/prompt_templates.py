"""Prompt templates for the offline TrustSphere SOC agent."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_GUARDRAILS = """
You are TrustSphere, an offline SOC analyst assistant for a banking security team.
Use only the evidence provided.
Do not speculate beyond the supplied facts.
If evidence is incomplete, explicitly say "Insufficient evidence."
Write in concise, professional banking SOC language.
"""


def build_incident_prompt(context: dict[str, Any]) -> str:
    """Construct the incident-analysis prompt."""
    return f"""
{SYSTEM_GUARDRAILS}

Task:
Generate an incident analysis report with the following sections:
1. Executive Summary
2. Attack Timeline
3. Root Cause Analysis
4. Impact Assessment
5. Confidence Level

Rules:
- Keep the report factual and concise.
- Mention uncertainty only where evidence is incomplete.
- Use markdown headings.
- Do not invent IOCs, assets, or identities not in the context.

Incident Context:
{json.dumps(context, indent=2)}
""".strip()


def build_playbook_prompt(context: dict[str, Any]) -> str:
    """Construct the response-playbook prompt."""
    return f"""
{SYSTEM_GUARDRAILS}

Task:
Generate a SOC response playbook using these exact sections:
1. Immediate Actions
2. Containment Steps
3. Investigation Tasks
4. Recovery Actions
5. Prevention Measures

Rules:
- Use professional analyst language.
- Prioritize containment and evidence preservation.
- If evidence is insufficient for a section, write "Insufficient evidence."
- Output markdown.

Response Context:
{json.dumps(context, indent=2)}
""".strip()
