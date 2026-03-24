"""Offline attack graph intelligence pipeline for TrustSphere."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .attack_graph_builder import AttackGraphBuilder
    from .event_linker import EventLinker
    from .graph_scoring import GraphRiskScorer
    from .graph_visualizer import GraphVisualizer
    from .mitre_mapper import MITREMapper
except ImportError:
    from attack_graph_builder import AttackGraphBuilder
    from event_linker import EventLinker
    from graph_scoring import GraphRiskScorer
    from graph_visualizer import GraphVisualizer
    from mitre_mapper import MITREMapper

try:
    from ..models.config import PROCESSED_DATA_DIR
except ImportError:
    from src.models.config import PROCESSED_DATA_DIR

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BASE_DIR / "outputs"


class AttackGraphPipeline:
    """Run the complete offline attack graph intelligence workflow."""

    def __init__(self) -> None:
        self.event_linker = EventLinker()
        self.graph_builder = AttackGraphBuilder()
        self.mitre_mapper = MITREMapper()
        self.graph_scorer = GraphRiskScorer()
        self.graph_visualizer = GraphVisualizer()

    def run(self, input_path: Path | None = None) -> dict[str, Any]:
        events_df = self._load_events(input_path)
        LOGGER.info("Events loaded: %s", len(events_df))
        linked_events = self.event_linker.link_events(events_df)
        graph = self.graph_builder.build_graph(events_df, linked_events)
        graph = self.mitre_mapper.annotate_graph(graph)
        chains = self.graph_builder.extract_attack_chains(graph)
        chains = self.mitre_mapper.annotate_chains(chains, graph)
        scores = self.graph_scorer.score_graph(graph, chains)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        self.graph_visualizer.export_graph(graph, OUTPUTS_DIR / "attack_graph.json")
        (OUTPUTS_DIR / "attack_paths.json").write_text(json.dumps(chains, indent=2), encoding="utf-8")
        self.graph_scorer.export_scores(scores, OUTPUTS_DIR / "graph_risk_scores.json")
        self.mitre_mapper.export_mapping(graph, OUTPUTS_DIR / "mitre_mapping.json")

        LOGGER.info("Linked relations: %s", len(linked_events))
        LOGGER.info("Attack chains detected: %s", len(chains))
        LOGGER.info("Critical chains: %s", scores.get("critical_chains", 0))
        LOGGER.info("Graph exported ✅")
        return {
            "events_loaded": len(events_df),
            "linked_relations": len(linked_events),
            "attack_chains": len(chains),
            "critical_chains": scores.get("critical_chains", 0),
        }

    def _load_events(self, input_path: Path | None = None) -> pd.DataFrame:
        candidate_paths = [input_path] if input_path else []
        candidate_paths.extend(
            [
                PROCESSED_DATA_DIR / "risk_output.csv",
                PROCESSED_DATA_DIR / "model_output.csv",
                PROCESSED_DATA_DIR / "normalized_logs.csv",
            ]
        )
        for candidate in candidate_paths:
            if candidate and candidate.exists():
                return self._normalize_frame(pd.read_csv(candidate))
        return self._synthetic_events()

    def _normalize_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        normalized.columns = [str(column).strip().lower() for column in normalized.columns]
        rename_map = {
            "ip_address": "ip",
            "device_type": "host",
            "event": "event_type",
        }
        normalized = normalized.rename(columns=rename_map)
        if "host" not in normalized.columns:
            normalized["host"] = normalized.get("device_type", "unknown-host")
        if "ip" not in normalized.columns:
            normalized["ip"] = normalized.get("ip_address", "0.0.0.0")
        if "user" not in normalized.columns and "user_id" in normalized.columns:
            normalized["user"] = normalized["user_id"]
        if "risk_level" not in normalized.columns:
            normalized["risk_level"] = pd.cut(
                pd.to_numeric(normalized.get("anomaly_score", 0.0), errors="coerce").fillna(0.0),
                bins=[-1, 0.3, 0.6, 0.8, 1.1],
                labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            ).astype(str)
        return normalized

    def _synthetic_events(self) -> pd.DataFrame:
        timestamps = pd.date_range("2026-03-24 08:00:00", periods=12, freq="30min")
        rows = [
            {"event_id": "evt-000001", "timestamp": timestamps[0], "user": "analyst-a", "host": "ws-10", "ip": "10.0.0.12", "event_type": "login_success", "anomaly_score": 0.08, "risk_level": "LOW"},
            {"event_id": "evt-000002", "timestamp": timestamps[1], "user": "analyst-a", "host": "ws-10", "ip": "10.0.0.12", "event_type": "file_access", "anomaly_score": 0.11, "risk_level": "LOW"},
            {"event_id": "evt-000003", "timestamp": timestamps[2], "user": "finance-x", "host": "laptop-22", "ip": "10.4.1.8", "event_type": "phishing_email", "anomaly_score": 0.41, "risk_level": "MEDIUM"},
            {"event_id": "evt-000004", "timestamp": timestamps[3], "user": "finance-x", "host": "laptop-22", "ip": "185.22.9.11", "event_type": "login_success_new_ip", "anomaly_score": 0.73, "risk_level": "HIGH"},
            {"event_id": "evt-000005", "timestamp": timestamps[4], "user": "finance-x", "host": "srv-auth-2", "ip": "185.22.9.11", "event_type": "privilege_change", "anomaly_score": 0.84, "risk_level": "CRITICAL"},
            {"event_id": "evt-000006", "timestamp": timestamps[5], "user": "finance-x", "host": "srv-auth-2", "ip": "10.9.7.5", "event_type": "admin_action", "anomaly_score": 0.88, "risk_level": "CRITICAL"},
            {"event_id": "evt-000007", "timestamp": timestamps[6], "user": "finance-x", "host": "db-core-1", "ip": "10.9.7.5", "event_type": "lateral_movement", "anomaly_score": 0.91, "risk_level": "CRITICAL"},
            {"event_id": "evt-000008", "timestamp": timestamps[7], "user": "finance-x", "host": "db-core-1", "ip": "10.9.7.5", "event_type": "data_exfiltration", "anomaly_score": 0.97, "risk_level": "CRITICAL"},
            {"event_id": "evt-000009", "timestamp": timestamps[8], "user": "developer-z", "host": "devbox-2", "ip": "10.0.1.33", "event_type": "login_failed", "anomaly_score": 0.37, "risk_level": "MEDIUM"},
            {"event_id": "evt-000010", "timestamp": timestamps[9], "user": "developer-z", "host": "devbox-2", "ip": "10.0.1.33", "event_type": "login_success", "anomaly_score": 0.44, "risk_level": "MEDIUM"},
            {"event_id": "evt-000011", "timestamp": timestamps[10], "user": "developer-z", "host": "build-7", "ip": "10.0.2.44", "event_type": "file_access", "anomaly_score": 0.58, "risk_level": "MEDIUM"},
            {"event_id": "evt-000012", "timestamp": timestamps[11], "user": "developer-z", "host": "build-7", "ip": "10.0.2.44", "event_type": "logout", "anomaly_score": 0.14, "risk_level": "LOW"},
        ]
        return pd.DataFrame(rows)


def _configure_logging() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUTS_DIR / "attack_pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


if __name__ == "__main__":
    _configure_logging()
    summary = AttackGraphPipeline().run()
    print(f"Events loaded: {summary['events_loaded']}")
    print(f"Linked relations: {summary['linked_relations']}")
    print(f"Attack chains detected: {summary['attack_chains']}")
    print(f"Critical chains: {summary['critical_chains']}")
    print("Graph exported ✅")
