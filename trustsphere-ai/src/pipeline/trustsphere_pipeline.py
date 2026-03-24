"""Unified TrustSphere intelligence pipeline callable from the serving layer."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ..attack_graph.attack_graph_builder import AttackGraphBuilder
from ..attack_graph.event_linker import EventLinker
from ..attack_graph.graph_scoring import GraphRiskScorer
from ..attack_graph.graph_visualizer import GraphVisualizer
from ..attack_graph.mitre_mapper import MITREMapper
from ..contracts import (
    AnomalyResult,
    AttackChain,
    AttackGraphEdge,
    AttackGraphNode,
    AttackGraphResult,
    FeatureMatrix,
    FeatureRow,
    IncidentReport,
    NormalizedLog,
    RiskResult,
)
from ..llm.incident_generator import IncidentReportGenerator
from ..llm.ollama_client import LocalLLM, write_install_notes
from ..llm.playbook_generator import PlaybookGenerator
from ..llm.report_exporter import ReportExporter
from ..models.config import PROCESSED_DATA_DIR
from ..models.inference_pipeline import UEBAInferencePipeline
from ..models.risk_engine import UEBARiskEngine

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BASE_DIR / "outputs"


class TrustSpherePipeline:
    """Single entrypoint for TrustSphere intelligence analysis."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else BASE_DIR
        self.outputs_dir = self.base_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.ueba_pipeline = UEBAInferencePipeline(self.base_dir / "saved_models")
        self.risk_engine = UEBARiskEngine()
        self.event_linker = EventLinker()
        self.graph_builder = AttackGraphBuilder()
        self.mitre_mapper = MITREMapper()
        self.graph_scorer = GraphRiskScorer()
        self.graph_visualizer = GraphVisualizer()
        self.llm = LocalLLM()
        self.incident_generator = IncidentReportGenerator(self.llm, self.outputs_dir)
        self.playbook_generator = PlaybookGenerator(self.llm, self.outputs_dir)
        self.report_exporter = ReportExporter(self.outputs_dir)
        write_install_notes(self.outputs_dir / "ollama_setup.txt")

    def analyze_incident(self, logs: list[NormalizedLog] | list[dict[str, Any]] | None = None) -> IncidentReport:
        normalized_logs = self._coerce_logs(logs or [])
        events_df = self._logs_to_frame(normalized_logs)
        feature_artifacts = self.ueba_pipeline.feature_engineer.transform(events_df)
        feature_matrix = self._to_feature_matrix(feature_artifacts)
        anomaly_entity_df = self.ueba_pipeline.predict(events_df)
        anomaly_results = self._to_anomaly_results(anomaly_entity_df)
        event_with_anomaly = self._attach_entity_scores(events_df, anomaly_entity_df)
        risk_df = self._build_risk_frame(event_with_anomaly)
        risk_results = self._to_risk_results(risk_df)
        graph_result = self._build_attack_graph(risk_df)
        context = self._build_context(graph_result)
        self._persist_context(context)
        incident_payload = self.incident_generator.generate(context)
        playbook_payload = self.playbook_generator.generate(context)
        exports = self.report_exporter.export(incident_payload, playbook_payload, context)

        incident_summary = json.loads(Path(exports["incident_summary"]).read_text(encoding="utf-8"))
        soc_dashboard = json.loads(Path(exports["soc_dashboard"]).read_text(encoding="utf-8"))

        return IncidentReport(
            incident_id=str(incident_payload["incident_id"]),
            timestamp=pd.to_datetime(incident_payload["timestamp"], utc=True).to_pydatetime(),
            severity=str(incident_payload["severity"]),
            confidence=str(incident_payload["confidence"]),
            anomaly_results=anomaly_results,
            risk_results=risk_results,
            feature_matrix=feature_matrix,
            attack_graph=graph_result,
            incident_summary=incident_summary,
            soc_dashboard=soc_dashboard,
            incident_report_path=str(exports["incident_report"]),
            response_playbook_path=str(exports["response_playbook"]),
        )

    def _coerce_logs(self, logs: list[NormalizedLog] | list[dict[str, Any]]) -> list[NormalizedLog]:
        if not logs:
            return self._sample_logs()
        return [log if isinstance(log, NormalizedLog) else NormalizedLog.model_validate(log) for log in logs]

    def _logs_to_frame(self, logs: list[NormalizedLog]) -> pd.DataFrame:
        frame = pd.DataFrame([log.model_dump(mode="python") for log in logs])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.tz_convert(None)
        frame = frame.dropna(subset=["timestamp"]).copy()
        frame["user"] = frame["user"].astype(str).str.lower()
        frame["host"] = frame["host"].astype(str).str.lower()
        frame["ip"] = frame["ip"].astype(str).str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.lower()
        frame["status"] = frame["status"].astype(str).str.lower()
        frame["process_name"] = frame["process_name"].astype(str).str.lower()
        frame["entity_id"] = frame["user"].fillna(frame["host"])
        frame["event_id"] = frame["event_id"].where(frame["event_id"].notna(), [f"evt-{index:06d}" for index in range(len(frame))])
        frame = frame.sort_values(["entity_id", "timestamp", "event_id"]).reset_index(drop=True)
        return frame

    def _attach_entity_scores(self, events_df: pd.DataFrame, anomaly_entity_df: pd.DataFrame) -> pd.DataFrame:
        event_frame = events_df.copy()
        scores = anomaly_entity_df[["entity_id", "anomaly_score", "anomaly_label"]].copy()
        merged = event_frame.merge(scores, on="entity_id", how="left")
        merged["anomaly_score"] = pd.to_numeric(merged["anomaly_score"], errors="coerce").fillna(0.0)
        merged["anomaly_label"] = pd.to_numeric(merged["anomaly_label"], errors="coerce").fillna(0).astype(int)
        return merged

    def _build_risk_frame(self, events_df: pd.DataFrame) -> pd.DataFrame:
        risk_input = events_df.copy()
        risk_input["entity_id"] = risk_input["entity_id"].astype(str)
        risk_df = self.risk_engine.evaluate_dataframe(risk_input)
        risk_df["risk_level"] = risk_df["risk_level"].astype(str).str.upper()
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        risk_df.to_csv(PROCESSED_DATA_DIR / "risk_output.csv", index=False)
        return risk_df

    def _build_attack_graph(self, risk_df: pd.DataFrame) -> AttackGraphResult:
        linked_events = self.event_linker.link_events(risk_df)
        graph = self.graph_builder.build_graph(risk_df, linked_events)
        graph = self.mitre_mapper.annotate_graph(graph)
        chains = self.graph_builder.extract_attack_chains(graph)
        chains = self.mitre_mapper.annotate_chains(chains, graph)
        scores = self.graph_scorer.score_graph(graph, chains)
        export_payload = self.graph_visualizer.export_graph(graph, self.outputs_dir / "attack_graph.json")
        self.graph_scorer.export_scores(scores, self.outputs_dir / "graph_risk_scores.json")
        self.graph_scorer.export_high_risk_chains(scores, self.outputs_dir / "high_risk_chains.parquet")
        self.mitre_mapper.export_mapping(graph, self.outputs_dir / "mitre_mapping.json")
        (self.outputs_dir / "attack_paths.json").write_text(json.dumps(scores.get("chain_scores", []), indent=2), encoding="utf-8")

        return AttackGraphResult(
            nodes=[AttackGraphNode.model_validate(node) for node in export_payload.get("nodes", [])],
            edges=[AttackGraphEdge.model_validate(edge) for edge in export_payload.get("edges", [])],
            chains=[AttackChain.model_validate(chain) for chain in scores.get("chain_scores", [])],
            critical_chains=int(scores.get("critical_chains", 0)),
        )

    def _build_context(self, attack_graph: AttackGraphResult) -> dict[str, Any]:
        chains = attack_graph.chains
        nodes = attack_graph.nodes
        top_chain = max(chains, key=lambda chain: float(chain.risk_score or 0.0), default=None)
        affected_users = self._unique_preserve(
            [event.get("user") for chain in chains for event in chain.sequence_of_events if event.get("user")]
        )
        timeline = sorted(
            [
                {
                    "timestamp": event.get("timestamp"),
                    "event_type": event.get("event_type"),
                    "user": event.get("user"),
                    "host": event.get("host"),
                    "risk_level": event.get("risk_level"),
                    "mitre_stage": event.get("mitre_tactic", "Unknown"),
                }
                for chain in chains
                for event in chain.sequence_of_events
            ],
            key=lambda item: str(item.get("timestamp", "")),
        )[:20]
        mitre_stages = self._unique_preserve([node.mitre_tactic for node in nodes if node.mitre_tactic and node.mitre_tactic != "Unknown"])
        key_evidence = self._unique_preserve(
            [
                relation.get("why_linked")
                for chain in chains
                for relation in chain.chain_relations
                if relation.get("why_linked")
            ]
            + [
                relation.get("risk_reason")
                for chain in chains
                for relation in chain.chain_relations
                if relation.get("risk_reason")
            ]
            + [
                f"{node.event_type or 'unknown_event'} on {node.event_id or node.id} scored {node.risk_score or 0} risk"
                for node in nodes
                if node.node_type == "alert"
            ]
        )[:12]
        context = {
            "threat_summary": {
                "detected_chains": len(chains),
                "highest_severity": (top_chain.severity if top_chain else "LOW") or "LOW",
                "highest_severity_score": float(top_chain.risk_score or 0.0) if top_chain else 0.0,
                "critical_chains": attack_graph.critical_chains,
            },
            "affected_users": affected_users,
            "attack_timeline": timeline,
            "risk_levels": {
                "critical_chains": attack_graph.critical_chains,
                "top_chain_levels": [chain.severity for chain in chains[:5] if chain.severity],
                "top_node_risks": [node.model_dump() for node in nodes if node.node_type == "alert"][:10],
            },
            "mitre_stages": mitre_stages,
            "key_evidence": key_evidence,
        }
        context_text = json.dumps(context, indent=2)
        context["context_text"] = context_text[:6000]
        return context

    def _persist_context(self, context: dict[str, Any]) -> None:
        threat_summary = {
            "summary": f"Detected {context['threat_summary']['detected_chains']} reconstructed attack chains.",
            "severity": context["threat_summary"]["highest_severity"],
            "indicators": context.get("mitre_stages", []),
            "evidence": context.get("key_evidence", []),
        }
        (self.outputs_dir / "threat_summary.json").write_text(json.dumps(threat_summary, indent=2), encoding="utf-8")

    def _to_feature_matrix(self, feature_artifacts) -> FeatureMatrix:
        rows = []
        selected = feature_artifacts.selected_features.reset_index()
        metadata = feature_artifacts.metadata_df.copy()
        merged = metadata.merge(selected, on="entity_id", how="left")
        for row in merged.to_dict(orient="records"):
            rows.append(
                FeatureRow(
                    entity_id=str(row["entity_id"]),
                    timestamp=pd.to_datetime(row["timestamp"], utc=True).to_pydatetime(),
                    features={
                        key: float(value)
                        for key, value in row.items()
                        if key not in {"entity_id", "timestamp"} and pd.notna(value)
                    },
                )
            )
        return FeatureMatrix.model_validate(
            {
                "rows": [row.model_dump(mode="python") for row in rows],
                "feature_columns": list(feature_artifacts.selected_columns),
            }
        )

    def _to_anomaly_results(self, anomaly_df: pd.DataFrame) -> list[AnomalyResult]:
        results: list[AnomalyResult] = []
        for row in anomaly_df.to_dict(orient="records"):
            results.append(
                AnomalyResult(
                    entity_id=str(row["entity_id"]),
                    timestamp=pd.to_datetime(row["timestamp"], utc=True).to_pydatetime(),
                    anomaly_score=float(row["anomaly_score"]),
                    anomaly_label=int(row["anomaly_label"]),
                )
            )
        return [AnomalyResult.model_validate(result.model_dump(mode="python")) for result in results]

    def _to_risk_results(self, risk_df: pd.DataFrame) -> list[RiskResult]:
        deduped = risk_df.sort_values(["entity_id", "timestamp"]).drop_duplicates(subset=["entity_id", "timestamp"], keep="last")
        results: list[RiskResult] = []
        for row in deduped.to_dict(orient="records"):
            results.append(
                RiskResult(
                    entity_id=str(row["entity_id"]),
                    timestamp=pd.to_datetime(row["timestamp"], utc=True).to_pydatetime(),
                    anomaly_score=float(row["anomaly_score"]),
                    risk_score=float(row["risk_score"]),
                    risk_level=str(row["risk_level"]),
                    behavioral_risk=float(row["behavioral_risk"]),
                    historical_risk=float(row["historical_risk"]),
                )
            )
        return [RiskResult.model_validate(result.model_dump(mode="python")) for result in results]

    def _unique_preserve(self, values: list[Any]) -> list[Any]:
        seen = set()
        ordered = []
        for value in values:
            if value in {None, "", "unknown", "Unknown"}:
                continue
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered

    def _sample_logs(self) -> list[NormalizedLog]:
        sample_rows = [
            {"timestamp": "2026-03-24T08:00:00Z", "user": "finance-x", "host": "laptop-22", "ip": "10.4.1.8", "event_type": "failed_login", "status": "failed", "device_type": "laptop", "location": "mumbai", "process_name": "outlook.exe", "failed_attempts": 7, "bytes_sent": 1200, "bytes_received": 4300, "login_success": False, "event_id": "evt-1"},
            {"timestamp": "2026-03-24T08:15:00Z", "user": "finance-x", "host": "laptop-22", "ip": "185.22.9.11", "event_type": "login_success_new_ip", "status": "success", "device_type": "unknown_device", "location": "singapore", "process_name": "cmd.exe", "failed_attempts": 0, "bytes_sent": 2500, "bytes_received": 6100, "login_success": True, "event_id": "evt-2"},
            {"timestamp": "2026-03-24T08:30:00Z", "user": "finance-x", "host": "srv-auth-2", "ip": "185.22.9.11", "event_type": "privilege_escalation", "status": "success", "device_type": "server", "location": "singapore", "process_name": "powershell.exe", "failed_attempts": 0, "bytes_sent": 5200, "bytes_received": 9400, "login_success": True, "event_id": "evt-3"},
            {"timestamp": "2026-03-24T08:45:00Z", "user": "finance-x", "host": "db-core-1", "ip": "185.22.9.11", "event_type": "data_exfiltration", "status": "success", "device_type": "server", "location": "singapore", "process_name": "scp.exe", "failed_attempts": 0, "bytes_sent": 450000, "bytes_received": 12000, "login_success": True, "event_id": "evt-4"},
        ]
        return [NormalizedLog.model_validate(row) for row in sample_rows]
