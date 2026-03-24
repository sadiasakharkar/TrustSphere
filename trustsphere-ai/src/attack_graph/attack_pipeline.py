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
    """Run the complete offline attack graph workflow from UEBA outputs."""

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
        self.graph_scorer.export_scores(scores, OUTPUTS_DIR / "graph_risk_scores.json")
        self.graph_scorer.export_high_risk_chains(scores, OUTPUTS_DIR / "high_risk_chains.parquet")
        self.mitre_mapper.export_mapping(graph, OUTPUTS_DIR / "mitre_mapping.json")
        (OUTPUTS_DIR / "attack_paths.json").write_text(json.dumps(scores.get("chain_scores", []), indent=2), encoding="utf-8")

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
        candidates = [input_path] if input_path else []
        candidates.extend(
            [
                PROCESSED_DATA_DIR / "ueba_scores.parquet",
                PROCESSED_DATA_DIR / "ueba_scores.csv",
                PROCESSED_DATA_DIR / "risk_output.csv",
                PROCESSED_DATA_DIR / "normalized_logs.csv",
            ]
        )
        for candidate in candidates:
            if candidate and candidate.exists():
                if candidate.suffix == ".parquet":
                    return self._normalize_frame(pd.read_parquet(candidate))
                return self._normalize_frame(pd.read_csv(candidate))
        return self._synthetic_events()

    def _normalize_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        normalized.columns = [str(column).strip().lower() for column in normalized.columns]
        if "user" not in normalized.columns and "entity_id" in normalized.columns:
            normalized["user"] = normalized["entity_id"]
        if "host" not in normalized.columns:
            normalized["host"] = normalized.get("device_type", normalized.get("entity_id", "unknown-host"))
        if "ip" not in normalized.columns:
            normalized["ip"] = normalized.get("ip_address", "0.0.0.0")
        if "process" not in normalized.columns:
            normalized["process"] = normalized.get("process_name", normalized.get("command", "unknown-process"))
        if "event_type" not in normalized.columns:
            normalized["event_type"] = "ueba_alert"
        if "risk_level" not in normalized.columns and "risk_score" in normalized.columns:
            normalized["risk_level"] = pd.cut(normalized["risk_score"], bins=[-1, 30, 70, 101], labels=["LOW", "MEDIUM", "CRITICAL"]).astype(str)
        elif "risk_level" not in normalized.columns:
            normalized["risk_level"] = pd.cut(pd.to_numeric(normalized.get("anomaly_score", 0.0), errors="coerce").fillna(0.0), bins=[-1, 0.3, 0.6, 0.8, 1.1], labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"]).astype(str)
        return normalized

    def _synthetic_events(self) -> pd.DataFrame:
        timestamps = pd.date_range("2026-03-24 08:00:00", periods=10, freq="15min")
        rows = [
            {"event_id": "evt-1", "timestamp": timestamps[0], "user": "finance-x", "host": "laptop-22", "ip": "10.4.1.8", "process": "outlook.exe", "event_type": "failed_login", "anomaly_score": 0.42, "risk_score": 38, "risk_level": "MEDIUM", "location": "mumbai"},
            {"event_id": "evt-2", "timestamp": timestamps[1], "user": "finance-x", "host": "laptop-22", "ip": "185.22.9.11", "process": "cmd.exe", "event_type": "login_success_new_ip", "anomaly_score": 0.71, "risk_score": 74, "risk_level": "HIGH", "location": "singapore"},
            {"event_id": "evt-3", "timestamp": timestamps[2], "user": "finance-x", "host": "srv-auth-2", "ip": "185.22.9.11", "process": "powershell.exe", "event_type": "privilege_escalation", "anomaly_score": 0.84, "risk_score": 86, "risk_level": "CRITICAL", "location": "singapore"},
            {"event_id": "evt-4", "timestamp": timestamps[3], "user": "finance-x", "host": "srv-auth-2", "ip": "185.22.9.11", "process": "mmc.exe", "event_type": "admin_action", "anomaly_score": 0.89, "risk_score": 91, "risk_level": "CRITICAL", "location": "singapore"},
            {"event_id": "evt-5", "timestamp": timestamps[4], "user": "finance-x", "host": "db-core-1", "ip": "185.22.9.11", "process": "sqlcmd.exe", "event_type": "lateral_movement", "anomaly_score": 0.93, "risk_score": 94, "risk_level": "CRITICAL", "location": "singapore"},
            {"event_id": "evt-6", "timestamp": timestamps[5], "user": "finance-x", "host": "db-core-1", "ip": "185.22.9.11", "process": "scp.exe", "event_type": "data_exfiltration", "anomaly_score": 0.98, "risk_score": 98, "risk_level": "CRITICAL", "location": "singapore"},
            {"event_id": "evt-7", "timestamp": timestamps[6], "user": "developer-z", "host": "devbox-2", "ip": "10.0.1.33", "process": "bash", "event_type": "login_success", "anomaly_score": 0.21, "risk_score": 18, "risk_level": "LOW", "location": "mumbai"},
            {"event_id": "evt-8", "timestamp": timestamps[7], "user": "developer-z", "host": "build-7", "ip": "10.0.1.33", "process": "python", "event_type": "file_access", "anomaly_score": 0.31, "risk_score": 28, "risk_level": "LOW", "location": "mumbai"},
            {"event_id": "evt-9", "timestamp": timestamps[8], "user": "developer-z", "host": "build-9", "ip": "10.0.1.33", "process": "ssh", "event_type": "lateral_movement", "anomaly_score": 0.61, "risk_score": 66, "risk_level": "MEDIUM", "location": "mumbai"},
            {"event_id": "evt-10", "timestamp": timestamps[9], "user": "developer-z", "host": "build-9", "ip": "10.0.1.33", "process": "tar", "event_type": "data_access", "anomaly_score": 0.58, "risk_score": 62, "risk_level": "MEDIUM", "location": "delhi"},
        ]
        return pd.DataFrame(rows)


def _configure_logging() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", handlers=[logging.FileHandler(OUTPUTS_DIR / "attack_pipeline.log"), logging.StreamHandler()])


if __name__ == "__main__":
    _configure_logging()
    summary = AttackGraphPipeline().run()
    print(f"Events loaded: {summary['events_loaded']}")
    print(f"Linked relations: {summary['linked_relations']}")
    print(f"Attack chains detected: {summary['attack_chains']}")
    print(f"Critical chains: {summary['critical_chains']}")
    print("Graph exported ✅")
