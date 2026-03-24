"""Graph scoring for TrustSphere SOC attack graph analytics."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


class GraphRiskScorer:
    """Compute node and chain risk using graph analytics and anomaly density."""

    def score_graph(self, graph: nx.MultiDiGraph, chains: list[dict[str, Any]]) -> dict[str, Any]:
        simple_graph = nx.DiGraph()
        for source, target, attrs in graph.edges(data=True):
            weight = float(attrs.get("confidence_score", 1.0))
            if simple_graph.has_edge(source, target):
                simple_graph[source][target]["weight"] = max(simple_graph[source][target]["weight"], weight)
            else:
                simple_graph.add_edge(source, target, weight=weight)
        pagerank = nx.pagerank(simple_graph, weight="weight") if simple_graph.number_of_nodes() else {}
        betweenness = nx.betweenness_centrality(simple_graph, weight="weight") if simple_graph.number_of_nodes() else {}

        node_scores: list[dict[str, Any]] = []
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "alert":
                continue
            anomaly_component = float(attrs.get("anomaly_score", 0.0)) * 100.0
            centrality_score = 50.0 * float(np.mean([pagerank.get(node, 0.0), betweenness.get(node, 0.0)]))
            node_risk = anomaly_component + centrality_score
            attrs["node_risk"] = round(node_risk, 2)
            node_scores.append(
                {
                    "node_id": node,
                    "event_id": attrs.get("event_id"),
                    "event_type": attrs.get("event_type"),
                    "risk_level": attrs.get("risk_level"),
                    "node_risk": attrs.get("node_risk"),
                    "centrality_score": round(centrality_score, 4),
                }
            )

        chain_scores = []
        for chain in chains:
            node_risks = [float(graph.nodes[event["node_id"]].get("node_risk", 0.0)) for event in chain.get("sequence_of_events", [])]
            path_length_weight = 5.0 * max(0, chain.get("path_length", 1) - 1)
            anomaly_density = 100.0 * float(chain.get("anomaly_density", 0.0))
            centrality_score = float(np.mean([pagerank.get(event["node_id"], 0.0) + betweenness.get(event["node_id"], 0.0) for event in chain.get("sequence_of_events", [])])) * 50.0 if chain.get("sequence_of_events") else 0.0
            risk_score = float(np.mean(node_risks)) + path_length_weight + anomaly_density + centrality_score if node_risks else 0.0
            chain_scores.append(
                {
                    "attack_chain_id": chain.get("attack_chain_id"),
                    "risk_score": round(risk_score, 2),
                    "severity": self._severity(risk_score),
                    **chain,
                }
            )
        return {
            "node_scores": node_scores,
            "chain_scores": chain_scores,
            "critical_chains": sum(1 for chain in chain_scores if chain["severity"] == "CRITICAL"),
        }

    def export_scores(self, payload: dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOGGER.info("Graph risk scores exported to %s", output_path)

    def export_high_risk_chains(self, payload: dict[str, Any], output_path: Path) -> Path:
        frame = pd.DataFrame(payload.get("chain_scores", []))
        if not frame.empty:
            frame = frame[frame["risk_score"] >= frame["risk_score"].median()].copy()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            frame.to_parquet(output_path, index=False)
        except Exception as exc:
            fallback = output_path.with_suffix(".csv")
            frame.to_csv(fallback, index=False)
            LOGGER.warning("Parquet export failed for %s (%s). Wrote CSV fallback to %s", output_path, exc, fallback)
        return output_path

    def _severity(self, score: float) -> str:
        if score >= 150:
            return "CRITICAL"
        if score >= 100:
            return "HIGH"
        if score >= 50:
            return "MEDIUM"
        return "LOW"
