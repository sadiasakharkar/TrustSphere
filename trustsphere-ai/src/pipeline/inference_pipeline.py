"""End-to-end offline inference pipeline scaffold."""

from src.features.feature_builder import build_features
from src.graph.attack_graph import build_attack_graph
from src.ingestion.log_parser import parse_log_record
from src.llm.reasoning_engine import generate_narrative
from src.models.anomaly_model import AnomalyModel
from src.models.risk_engine import compute_risk


def run_inference(record: str) -> dict:
    event = parse_log_record(record)
    features = build_features(event)
    anomaly = AnomalyModel().predict(features)
    risk = compute_risk(anomaly)
    graph = build_attack_graph({"event": event, "risk": risk})
    narrative = generate_narrative({"event": event, "risk": risk, "graph": graph})
    return {
        "event": event,
        "features": features,
        "anomaly": anomaly,
        "risk": risk,
        "graph": graph,
        "narrative": narrative,
    }
