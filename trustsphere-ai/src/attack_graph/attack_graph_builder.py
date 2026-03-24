"""Attack graph builder for TrustSphere."""

from __future__ import annotations

from collections import deque
import logging
from typing import Any

import networkx as nx
import pandas as pd

LOGGER = logging.getLogger(__name__)
RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class AttackGraphBuilder:
    """Build directed attack graphs from linked enterprise events."""

    def __init__(self, noise_risk_levels: tuple[str, ...] = ("HIGH", "CRITICAL")) -> None:
        self.noise_risk_levels = set(noise_risk_levels)

    def build_graph(self, events_df: pd.DataFrame, linked_events: list[dict[str, Any]]) -> nx.DiGraph:
        """Create a directed graph with event, user, and host nodes."""
        graph = nx.DiGraph()
        frame = self._prepare_events(events_df)
        event_lookup = frame.set_index("event_id").to_dict("index")

        for row in frame.itertuples(index=False):
            event_node = f"event::{row.event_id}"
            user_node = f"user::{row.user}"
            host_node = f"host::{row.host}"
            graph.add_node(
                event_node,
                node_type="event",
                event_id=row.event_id,
                timestamp=row.timestamp.isoformat(),
                event_type=row.event_type,
                risk_level=row.risk_level,
                anomaly_score=float(row.anomaly_score),
                user=row.user,
                host=row.host,
            )
            graph.add_node(user_node, node_type="user", user=row.user)
            graph.add_node(host_node, node_type="host", host=row.host)
            graph.add_edge(user_node, event_node, relation_type="performed", time_delta=0.0, confidence_score=1.0)
            graph.add_edge(event_node, host_node, relation_type="targeted_host", time_delta=0.0, confidence_score=1.0)

        for link in linked_events:
            source_id = f"event::{link['source_event_id']}"
            target_id = f"event::{link['target_event_id']}"
            if source_id not in graph or target_id not in graph:
                continue
            source_ts = pd.to_datetime(event_lookup[link["source_event_id"]]["timestamp"])
            target_ts = pd.to_datetime(event_lookup[link["target_event_id"]]["timestamp"])
            if target_ts < source_ts:
                continue
            graph.add_edge(
                source_id,
                target_id,
                relation_type=link["relation_type"],
                time_delta=float(link["time_delta_hours"]),
                confidence_score=float(link["confidence_score"]),
                why_linked=link["why_linked"],
                risk_reason=link["risk_reason"],
            )

        self._reduce_noise(graph)
        LOGGER.info("Graph built with %s nodes and %s edges", graph.number_of_nodes(), graph.number_of_edges())
        return graph

    def extract_attack_chains(self, graph: nx.DiGraph, max_depth: int = 6) -> list[dict[str, Any]]:
        """Extract high-risk attack chains around significant event nodes."""
        chains: list[dict[str, Any]] = []
        seeds = [
            node for node, attrs in graph.nodes(data=True)
            if attrs.get("node_type") == "event" and attrs.get("risk_level") in self.noise_risk_levels
        ]

        for seed in seeds:
            sub_nodes = self._collect_chain_nodes(graph, seed, max_depth=max_depth)
            event_nodes = [node for node in sub_nodes if graph.nodes[node].get("node_type") == "event"]
            ordered_events = sorted(event_nodes, key=lambda node: graph.nodes[node].get("timestamp", ""))
            if len(ordered_events) < 2:
                continue
            edge_details = []
            for source, target in zip(ordered_events[:-1], ordered_events[1:]):
                if graph.has_edge(source, target):
                    edge_details.append(graph.edges[source, target])
            linked_event_count = len(edge_details)
            confidence = 0.0 if len(ordered_events) == 0 else linked_event_count / len(ordered_events)
            chain = {
                "chain_id": f"chain-{len(chains) + 1:03d}",
                "seed_node": seed,
                "events": [self._event_summary(graph, node) for node in ordered_events],
                "linked_events": linked_event_count,
                "total_events": len(ordered_events),
                "chain_confidence": round(confidence, 4),
                "why_linked": [edge.get("why_linked", "") for edge in edge_details],
                "risk_reason": [edge.get("risk_reason", "") for edge in edge_details],
            }
            chains.append(chain)

        LOGGER.info("Attack chains detected: %s", len(chains))
        return chains

    def _prepare_events(self, events_df: pd.DataFrame) -> pd.DataFrame:
        frame = events_df.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).copy()
        frame["risk_level"] = frame.get("risk_level", "LOW").astype(str).str.upper()
        frame["anomaly_score"] = pd.to_numeric(frame.get("anomaly_score", 0.0), errors="coerce").fillna(0.0)
        frame["event_id"] = frame.get("event_id", frame.index.map(lambda idx: f"evt-{idx:06d}"))
        return frame

    def _reduce_noise(self, graph: nx.DiGraph) -> None:
        removable: list[str] = []
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "event":
                continue
            if attrs.get("risk_level") in self.noise_risk_levels:
                continue
            if graph.degree(node) <= 1 and float(attrs.get("anomaly_score", 0.0)) < 0.2:
                removable.append(node)
        for node in removable:
            graph.remove_node(node)
        if removable:
            LOGGER.info("Noise reduction removed %s low-risk isolated nodes", len(removable))

    def _collect_chain_nodes(self, graph: nx.DiGraph, seed: str, max_depth: int) -> set[str]:
        visited = {seed}
        queue = deque([(seed, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            neighbors = list(graph.predecessors(node)) + list(graph.successors(node))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                if graph.nodes[neighbor].get("node_type") == "event":
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return visited

    def _event_summary(self, graph: nx.DiGraph, node: str) -> dict[str, Any]:
        attrs = graph.nodes[node]
        return {
            "node_id": node,
            "event_id": attrs.get("event_id"),
            "timestamp": attrs.get("timestamp"),
            "event_type": attrs.get("event_type"),
            "risk_level": attrs.get("risk_level"),
            "anomaly_score": attrs.get("anomaly_score"),
            "user": attrs.get("user"),
            "host": attrs.get("host"),
        }
