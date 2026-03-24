"""MITRE ATT&CK mapping for TrustSphere attack graph intelligence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

LOGGER = logging.getLogger(__name__)

MITRE_MAPPING: dict[str, dict[str, str]] = {
    "failed_login": {"mitre_tactic": "Credential Access", "mitre_technique": "Brute Force (T1110)", "mitre_id": "T1110"},
    "login_failed": {"mitre_tactic": "Credential Access", "mitre_technique": "Brute Force (T1110)", "mitre_id": "T1110"},
    "privilege_escalation": {"mitre_tactic": "Privilege Escalation", "mitre_technique": "Exploitation for Privilege Escalation (T1068)", "mitre_id": "T1068"},
    "privilege_change": {"mitre_tactic": "Privilege Escalation", "mitre_technique": "Exploitation for Privilege Escalation (T1068)", "mitre_id": "T1068"},
    "lateral_movement": {"mitre_tactic": "Lateral Movement", "mitre_technique": "Remote Services (T1021)", "mitre_id": "T1021"},
    "data_exfiltration": {"mitre_tactic": "Exfiltration", "mitre_technique": "Exfiltration Over C2 Channel (T1041)", "mitre_id": "T1041"},
}


class MITREMapper:
    """Attach MITRE tags to alert nodes and reconstructed chains."""

    def annotate_graph(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "alert":
                continue
            mapping = MITRE_MAPPING.get(str(attrs.get("event_type", "")).lower(), {})
            attrs["mitre_tactic"] = mapping.get("mitre_tactic", "Unknown")
            attrs["mitre_technique"] = mapping.get("mitre_technique", "Insufficient evidence")
            attrs["mitre_id"] = mapping.get("mitre_id", "Unknown")
        return graph

    def annotate_chains(self, chains: list[dict[str, Any]], graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
        for chain in chains:
            mitre_ids: list[str] = []
            for event in chain.get("sequence_of_events", []):
                attrs = graph.nodes.get(event["node_id"], {})
                event["mitre_tactic"] = attrs.get("mitre_tactic", "Unknown")
                event["mitre_technique"] = attrs.get("mitre_technique", "Insufficient evidence")
                event["mitre_id"] = attrs.get("mitre_id", "Unknown")
                mitre_ids.append(event["mitre_id"])
            chain["mitre_tags"] = sorted({tag for tag in mitre_ids if tag != "Unknown"})
        return chains

    def export_mapping(self, graph: nx.MultiDiGraph, output_path: Path) -> None:
        payload = []
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "alert":
                continue
            payload.append(
                {
                    "node_id": node,
                    "event_id": attrs.get("event_id"),
                    "event_type": attrs.get("event_type"),
                    "mitre_tactic": attrs.get("mitre_tactic"),
                    "mitre_technique": attrs.get("mitre_technique"),
                    "mitre_id": attrs.get("mitre_id"),
                }
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOGGER.info("MITRE mapping exported to %s", output_path)
