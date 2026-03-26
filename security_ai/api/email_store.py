from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


HISTORY_FILE = Path(__file__).resolve().parent / "email_history.json"

MOCK_INBOX = [
    {
        "id": "mail-001",
        "sender": "bank@secure.com",
        "subject": "Verify your account urgently",
        "body": "Click http://fake-bank.xyz and enter password immediately to keep your banking access active.",
    },
    {
        "id": "mail-002",
        "sender": "hr@company.com",
        "subject": "Salary Update",
        "body": "Please review your salary details in the attached document and confirm the latest compensation breakdown.",
    },
    {
        "id": "mail-003",
        "sender": "support@paypal.com",
        "subject": "Unusual login detected",
        "body": "We noticed a suspicious login. Verify now at http://phishing-login.xyz to secure your account.",
    },
]


def get_inbox() -> list[dict[str, Any]]:
    return MOCK_INBOX


def get_history() -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_history(entry: dict[str, Any]) -> None:
    history = get_history()
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def clear_history() -> None:
    HISTORY_FILE.write_text("[]", encoding="utf-8")


def build_email_analysis(
    detector_result: dict[str, Any],
    *,
    email_text: str,
    subject: str = "",
    sender: str = "unknown@example.com",
) -> dict[str, Any]:
    probability = float(detector_result.get("phishing_probability", 0.0))
    risk_score = round(probability * 100.0, 2)

    if probability >= 0.75:
        severity = "HIGH"
    elif probability >= 0.4:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    actions = {
        "HIGH": [
            "Escalate to SOC analyst",
            "Quarantine suspicious email",
            "Block sender and embedded domains",
        ],
        "MEDIUM": [
            "Flag email for analyst review",
            "Warn recipient before interaction",
        ],
        "LOW": [
            "Log event for monitoring",
        ],
    }[severity]

    return {
        "input": email_text,
        "sender": sender,
        "subject": subject or "Analyzed email",
        "risk_score": risk_score,
        "severity": severity,
        "models": {
            "email_detector": round(probability, 4),
        },
        "actions": actions,
        "time": datetime.utcnow().replace(microsecond=0).isoformat(),
        "label": detector_result.get("label", "safe"),
    }
