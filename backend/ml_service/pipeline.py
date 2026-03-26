import numpy as np
from model_runner import run_all_models

def preprocess(data):
    return data.get("input", [])

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

    return {
        "risk_score": risk_score,
        "severity": severity,
        "models": model_results
    }