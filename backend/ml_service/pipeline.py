import numpy as np
from model_runner import run_all_models
from action_engine import take_action
from history_store import save_history
from datetime import datetime

def preprocess(data):
    raw_input = data.get("input", "")
    if raw_input is None:
        return ""
    return str(raw_input)


def generate_reasons(text, model_results, severity):
    normalized_text = (text or "").lower()
    reasons = []

    if any(token in normalized_text for token in ("http://", "https://", "www.", ".com", ".net", ".org")):
        reasons.append("Suspicious link detected")

    if any(token in normalized_text for token in ("urgent", "immediately", "asap", "action required", "verify now")):
        reasons.append("Urgent language used")

    if any(token in normalized_text for token in ("password", "otp", "credential", "credentials", "login", "bank details", "verify account")):
        reasons.append("Credential request found")

    high_risk_models = [name.replace("_", " ") for name, score in model_results.items() if float(score) > 0.6]
    if high_risk_models:
        reasons.append(f"High-risk model signals: {', '.join(high_risk_models)}")

    if not reasons:
        if severity in {"HIGH", "MEDIUM"}:
            reasons.append("General anomaly detected")
        else:
            reasons.append("No strong fraud indicators detected")

    return reasons

def run_pipeline(data):

    x = preprocess(data)

    model_results = run_all_models(x)

    scores = list(model_results.values())

    if len(scores) == 0:
        return {"error": "No models found"}

    risk_score = float(np.mean(scores))

# NEW LOGIC
    high_count = sum(1 for s in scores if s > 0.6)

    if high_count >= 2:
        severity = "HIGH"
    elif high_count == 1:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    actions = take_action(model_results, severity)
    reasons = generate_reasons(x, model_results, severity)

    entry = {
        "input": x,
        "risk_score": risk_score,
        "score": risk_score,
        "severity": severity,
        "reasons": reasons,
        "models": model_results,
        "actions": actions,
        "time": datetime.now().isoformat(timespec="seconds")
    }

    save_history(entry)

    return {
        "score": risk_score,
        "risk_score": risk_score,
        "severity": severity,
        "reasons": reasons,
        "models": model_results,
        "actions_taken": actions
    }
