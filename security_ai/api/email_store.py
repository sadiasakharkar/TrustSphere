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


def extract_risk_drivers(email_text: str, model_results: dict[str, Any] | None = None) -> list[str]:
    text_lower = str(email_text or "").lower()
    drivers: list[str] = []

    keyword_map = {
        "http": "http link",
        "https": "https link",
        "urgent": "urgent",
        "immediately": "immediately",
        "action required": "action required",
        "password": "password",
        "otp": "otp",
        "pin": "pin",
        "credentials": "credentials",
        "verify": "verify",
        "login": "login",
        "account": "account",
        "gift card": "gift card",
        "wire": "wire",
    }

    for token, label in keyword_map.items():
        if token in text_lower and label not in drivers:
            drivers.append(label)

    for model, score in (model_results or {}).items():
        try:
            if float(score) > 0.6:
                drivers.append(f"{model} anomaly")
        except Exception:
            continue

    return drivers or ["no major indicators"]


def summarize_reasons(email_text: str, risk_drivers: list[str], severity: str) -> list[str]:
    text_lower = str(email_text or "").lower()
    reasons: list[str] = []

    if any(token in text_lower for token in ("http://", "https://", "login", "verify", "account")):
        reasons.append("Suspicious account verification or login lure detected")

    if any(token in text_lower for token in ("urgent", "immediately", "action required")):
        reasons.append("Urgent language is pressuring the recipient to act quickly")

    if any(token in text_lower for token in ("password", "otp", "pin", "credentials")):
        reasons.append("Credential harvesting language detected")

    if any("anomaly" in driver for driver in risk_drivers):
        reasons.append("The email classifier produced an elevated phishing score")

    if not reasons:
        reasons.append(
            "High-risk content patterns were detected across the message"
            if severity in {"HIGH", "MEDIUM"}
            else "No major phishing indicators were found"
        )

    return reasons


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
    model_scores = {
        "email_detector": round(probability, 4),
    }
    risk_drivers = extract_risk_drivers(email_text, model_scores)
    reasons = summarize_reasons(email_text, risk_drivers, severity)

    return {
        "input": email_text,
        "sender": sender,
        "subject": subject or "Analyzed email",
        "risk_score": risk_score,
        "severity": severity,
        "models": model_scores,
        "actions": actions,
        "risk_drivers": risk_drivers,
        "reasons": reasons,
        "time": datetime.utcnow().replace(microsecond=0).isoformat(),
        "label": detector_result.get("label", "safe"),
    }
