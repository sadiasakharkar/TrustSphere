"""Risk scoring for TrustSphere attack graphs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

LOGGER = logging.getLogger(__name__)
RISK_LEVEL_SCORE = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
MITRE_STAGE_WEIGHT = {
    "TA0001": 1.1,
    "TA0003": 1.0,
    "TA0004": 1.25,
    "TA0006": 1.1,
    "TA0008": 1.35,
    "TA0009": 1.15,
    "TA0010": 1.4,
    "Unknown": 0.9,
}


class GraphRiskScorer:
    """Compute node and chain risk from graph structure and UEBA signals."""

    def __init__(self, ueba_risk_weight: float = 1.15) -> None:
        self.ueba_risk_weight = ueba_risk_weight

    def score_graph(self, graph: nx.DiGraph, chains: list[dict[str, Any]]) -> dict[str, Any]:
        event_nodes = [node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "event"]
        degree = nx.degree_centrality(graph)
        betweenness = nx.betweenness_centrality(graph)
        pagerank = nx.pagerank(graph) if graph.number_of_nodes() else {}

        node_scores: list[dict[str, Any]] = []
        for node in event_nodes:
            attrs = graph.nodes[node]
            centrality = float(np.mean([degree.get(node, 0.0), betweenness.get(node, 0.0), pagerank.get(node, 0.0)]))
            base_risk = float(attrs.get("anomaly_score", 0.0)) * 100.0
            risk_weight = RISK_LEVEL_SCORE.get(str(attrs.get("risk_level", "LOW")).upper(), 0.25)
            node_risk = min(100.0, base_risk * self.ueba_risk_weight * max(0.2, centrality + risk_weight))
            attrs["node_risk"] = round(node_risk, 2)
            attrs["centrality"] = round(centrality, 4)
            node_scores.append(
                {
                    "node_id": node,
                    "event_id": attrs.get("event_id"),
                    "event_type": attrs.get("event_type"),
                    "risk_level": attrs.get("risk_level"),
                    "node_risk": attrs["node_risk"],
                    "centrality": attrs["centrality"],
                }
            )

        chain_scores = self._score_chains(graph, chains)
        summary = {
            "node_scores": node_scores,
            "chain_scores": chain_scores,
            "critical_chains": sum(1 for chain in chain_scores if chain["severity_level"] == "CRITICAL"),
        }
        return summary

    def export_scores(self, payload: dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOGGER.info("Graph risk scores exported to %s", output_path)

    def _score_chains(self, graph: nx.DiGraph, chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for chain in chains:
            node_risks = []
            stage_weights = []
            for event in chain.get("events", []):
                attrs = graph.nodes.get(event["node_id"], {})
                node_risks.append(float(attrs.get("node_risk", 0.0)))
                stage_weights.append(MITRE_STAGE_WEIGHT.get(attrs.get("mitre_stage", "Unknown"), 0.9))
            avg_node_risk = float(np.mean(node_risks)) if node_risks else 0.0
            avg_stage_weight = float(np.mean(stage_weights)) if stage_weights else 0.9
            chain_length = max(1, len(chain.get("events", [])))
            severity_score = min(100.0, avg_node_risk * (chain_length / 3.0) * avg_stage_weight)
            results.append(
                {
                    "chain_id": chain.get("chain_id"),
                    "severity_score": round(severity_score, 2),
                    "severity_level": self._to_severity_label(severity_score),
                    "chain_confidence": chain.get("chain_confidence", 0.0),
                    "events": chain.get("events", []),
                    "mitre_stage": chain.get("mitre_stage", []),
                    "why_linked": chain.get("why_linked", []),
                    "risk_reason": chain.get("risk_reason", []),
                }
            )
        return results

    def _to_severity_label(self, score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        if score >= 60:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        return "LOW"
