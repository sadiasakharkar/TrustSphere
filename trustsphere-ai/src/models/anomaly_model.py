"""Anomaly model scaffold."""


class AnomalyModel:
    def predict(self, features: dict) -> dict:
        return {"anomaly_score": 0.42, "is_anomalous": False, "features": features}
