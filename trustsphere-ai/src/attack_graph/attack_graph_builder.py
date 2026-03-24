"""Attack graph builder and chain reconstruction for TrustSphere."""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx
import pandas as pd

LOGGER = logging.getLogger(__name__)


class AttackGraphBuilder:
    """Build a directed multigraph and reconstruct attack chains."""

    def __init__(self, seed_risk_levels: tuple[str, ...] = ("HIGH", "CRITICAL")) -> None:
        self.seed_risk_levels = set(seed_risk_levels)

    def build_graph(self, events_df: pd.DataFrame, linked_events: list[dict[str, Any]]) -> nx.MultiDiGraph:
        graph = nx.MultiDiGraph()
        frame = self._prepare_events(events_df)
        lookup = frame.set_index("event_id").to_dict("index")

        for row in frame.itertuples(index=False):
            alert_node = f"alert::{row.event_id}"
            user_node = f"user::{row.user}"
            host_node = f"host::{row.host}"
            ip_node = f"ip::{row.ip}"
            process_node = f"process::{row.process}"

            graph.add_node(user_node, node_type="user", entity_id=row.user, risk_level=row.risk_level)
            graph.add_node(host_node, node_type="host", entity_id=row.host, risk_level=row.risk_level)
            graph.add_node(ip_node, node_type="ip", entity_id=row.ip, risk_level=row.risk_level)
            graph.add_node(process_node, node_type="process", entity_id=row.process, risk_level=row.risk_level)
            graph.add_node(
                alert_node,
                node_type="alert",
                event_id=row.event_id,
                timestamp=row.timestamp.isoformat(),
                event_type=row.event_type,
                user=row.user,
                host=row.host,
                ip=row.ip,
                process=row.process,
                risk_level=row.risk_level,
                risk_score=float(row.risk_score),
                anomaly_score=float(row.anomaly_score),
            )

            graph.add_edge(user_node, ip_node, relation_type="login_from", timestamp=row.timestamp.isoformat())
            graph.add_edge(user_node, host_node, relation_type="connected_to", timestamp=row.timestamp.isoformat())
            graph.add_edge(process_node, host_node, relation_type="executed_on", timestamp=row.timestamp.isoformat())
            graph.add_edge(user_node, alert_node, relation_type="triggered_alert", timestamp=row.timestamp.isoformat())
            graph.add_edge(alert_node, process_node, relation_type="alert_process", timestamp=row.timestamp.isoformat())

        for link in linked_events:
            source_node = f"alert::{link['source_event_id']}"
            target_node = f"alert::{link['target_event_id']}"
            if source_node not in graph or target_node not in graph:
                continue
            source_ts = pd.to_datetime(lookup[link["source_event_id"]]["timestamp"])
            target_ts = pd.to_datetime(lookup[link["target_event_id"]]["timestamp"])
            if target_ts < source_ts:
                continue
            graph.add_edge(
                source_node,
                target_node,
                relation_type=link["relation_type"],
                time_delta_minutes=float(link["time_delta_minutes"]),
                confidence_score=float(link["confidence_score"]),
                why_linked=link["why_linked"],
                risk_reason=link["risk_reason"],
            )

        LOGGER.info("Graph built with %s nodes and %s edges", graph.number_of_nodes(), graph.number_of_edges())
        return graph

    def extract_attack_chains(self, graph: nx.MultiDiGraph, max_depth: int = 8) -> list[dict[str, Any]]:
        chains: list[dict[str, Any]] = []
        seeds = [
            node
            for node, attrs in graph.nodes(data=True)
            if attrs.get("node_type") == "alert" and str(attrs.get("risk_level", "LOW")).upper() in self.seed_risk_levels
        ]
        if not seeds:
            candidate_alerts = [
                node
                for node, attrs in graph.nodes(data=True)
                if attrs.get("node_type") == "alert" and graph.out_degree(node) > 0
            ]
            seeds = sorted(
                candidate_alerts,
                key=lambda node: (
                    float(graph.nodes[node].get("risk_score", 0.0)),
                    float(graph.nodes[node].get("anomaly_score", 0.0)),
                ),
                reverse=True,
            )[:3]
        for seed in seeds:
            path_nodes = self._dfs_paths(graph, seed, max_depth)
            if len(path_nodes) < 2:
                continue
            ordered = sorted(path_nodes, key=lambda node: graph.nodes[node].get("timestamp", ""))
            alert_nodes = [node for node in ordered if graph.nodes[node].get("node_type") == "alert"]
            if len(alert_nodes) < 2:
                continue
            entities = sorted({graph.nodes[node].get("user") for node in alert_nodes if graph.nodes[node].get("user")} | {graph.nodes[node].get("host") for node in alert_nodes if graph.nodes[node].get("host")} | {graph.nodes[node].get("ip") for node in alert_nodes if graph.nodes[node].get("ip")})
            start_time = graph.nodes[alert_nodes[0]].get("timestamp")
            end_time = graph.nodes[alert_nodes[-1]].get("timestamp")
            relations = self._chain_edges(graph, alert_nodes)
            density = len(relations) / max(1, len(alert_nodes))
            chains.append(
                {
                    "attack_chain_id": f"attack-chain-{len(chains) + 1:03d}",
                    "sequence_of_events": [self._event_summary(graph, node) for node in alert_nodes],
                    "entities_involved": entities,
                    "start_time": start_time,
                    "end_time": end_time,
                    "path_length": len(alert_nodes),
                    "anomaly_density": round(density, 4),
                    "risk_propagation": round(sum(graph.nodes[node].get("anomaly_score", 0.0) for node in alert_nodes), 4),
                    "chain_relations": relations,
                }
            )
        LOGGER.info("Attack chains detected: %s", len(chains))
        return chains

    def _prepare_events(self, events_df: pd.DataFrame) -> pd.DataFrame:
        frame = events_df.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).copy()
        frame["user"] = self._series(frame, "user", frame.get("user_id"), "unknown-user").astype(str).str.lower()
        frame["host"] = self._series(frame, "host", frame.get("host_id", frame.get("device_type")), "unknown-host").astype(str).str.lower()
        frame["ip"] = self._series(frame, "ip", frame.get("ip_address"), "0.0.0.0").astype(str).str.lower()
        frame["process"] = self._series(frame, "process", frame.get("process_name", frame.get("command")), "unknown-process").astype(str).str.lower()
        frame["event_type"] = self._series(frame, "event_type", None, "unknown_event").astype(str).str.lower()
        frame["risk_level"] = self._series(frame, "risk_level", None, "LOW").astype(str).str.upper()
        frame["risk_score"] = pd.to_numeric(self._series(frame, "risk_score", None, 0.0), errors="coerce").fillna(0.0)
        frame["anomaly_score"] = pd.to_numeric(self._series(frame, "anomaly_score", None, 0.0), errors="coerce").fillna(0.0)
        frame["event_id"] = self._series(frame, "event_id", None, None)
        frame["event_id"] = [value if value not in {None, "None", "nan"} else f"evt-{idx:06d}" for idx, value in enumerate(frame["event_id"])]
        return frame

    def _dfs_paths(self, graph: nx.MultiDiGraph, seed: str, max_depth: int) -> set[str]:
        visited: set[str] = set()
        stack = [(seed, 0)]
        while stack:
            node, depth = stack.pop()
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            for _, neighbor, edge_attrs in graph.out_edges(node, data=True):
                if pd.isna(edge_attrs.get("time_delta_minutes", 0.0)):
                    continue
                if graph.nodes[neighbor].get("node_type") == "alert":
                    stack.append((neighbor, depth + 1))
        return visited

    def _chain_edges(self, graph: nx.MultiDiGraph, alert_nodes: list[str]) -> list[dict[str, Any]]:
        relations: list[dict[str, Any]] = []
        for source, target in zip(alert_nodes[:-1], alert_nodes[1:]):
            edge_bundle = graph.get_edge_data(source, target, default={})
            for _, attrs in edge_bundle.items():
                relations.append(
                    {
                        "source": source,
                        "target": target,
                        "relation_type": attrs.get("relation_type"),
                        "why_linked": attrs.get("why_linked"),
                        "risk_reason": attrs.get("risk_reason"),
                    }
                )
        return relations

    def _event_summary(self, graph: nx.MultiDiGraph, node: str) -> dict[str, Any]:
        attrs = graph.nodes[node]
        return {
            "node_id": node,
            "event_id": attrs.get("event_id"),
            "timestamp": attrs.get("timestamp"),
            "event_type": attrs.get("event_type"),
            "risk_level": attrs.get("risk_level"),
            "anomaly_score": attrs.get("anomaly_score"),
            "risk_score": attrs.get("risk_score"),
            "user": attrs.get("user"),
            "host": attrs.get("host"),
            "ip": attrs.get("ip"),
            "process": attrs.get("process"),
        }

    def _series(self, frame: pd.DataFrame, primary: str, secondary: pd.Series | None, default: Any) -> pd.Series:
        if primary in frame.columns:
            return frame[primary]
        if isinstance(secondary, pd.Series):
            return secondary
        return pd.Series([default] * len(frame), index=frame.index)
