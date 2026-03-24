"""Risk scoring scaffold."""


def compute_risk(anomaly_output: dict) -> dict:
    score = round(float(anomaly_output.get("anomaly_score", 0.0)) * 100, 2)
    return {"risk_score": score, "severity": "low" if score < 50 else "medium"}
