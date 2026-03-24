"""MITRE ATT&CK mapping for TrustSphere attack graphs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

LOGGER = logging.getLogger(__name__)

MITRE_MAPPING: dict[str, dict[str, str]] = {
    "login_failed": {"mitre_tactic": "Credential Access", "mitre_technique": "Brute Force (T1110)", "mitre_stage": "TA0006"},
    "failed_login": {"mitre_tactic": "Credential Access", "mitre_technique": "Brute Force (T1110)", "mitre_stage": "TA0006"},
    "login_success_new_ip": {"mitre_tactic": "Initial Access", "mitre_technique": "Valid Accounts (T1078)", "mitre_stage": "TA0001"},
    "login_success": {"mitre_tactic": "Initial Access", "mitre_technique": "Valid Accounts (T1078)", "mitre_stage": "TA0001"},
    "phishing_email": {"mitre_tactic": "Initial Access", "mitre_technique": "Phishing (T1566)", "mitre_stage": "TA0001"},
    "privilege_escalation": {"mitre_tactic": "Privilege Escalation", "mitre_technique": "Exploitation for Privilege Escalation (T1068)", "mitre_stage": "TA0004"},
    "privilege_change": {"mitre_tactic": "Privilege Escalation", "mitre_technique": "Additional Cloud Roles (T1098.003)", "mitre_stage": "TA0004"},
    "lateral_movement": {"mitre_tactic": "Lateral Movement", "mitre_technique": "Remote Services (T1021)", "mitre_stage": "TA0008"},
    "admin_action": {"mitre_tactic": "Persistence", "mitre_technique": "Account Manipulation (T1098)", "mitre_stage": "TA0003"},
    "data_exfiltration": {"mitre_tactic": "Exfiltration", "mitre_technique": "Exfiltration Over Web Service (T1567)", "mitre_stage": "TA0010"},
    "file_access": {"mitre_tactic": "Collection", "mitre_technique": "Data from Information Repositories (T1213)", "mitre_stage": "TA0009"},
}


class MITREMapper:
    """Attach MITRE ATT&CK metadata to graph nodes and chains."""

    def annotate_graph(self, graph: nx.DiGraph) -> nx.DiGraph:
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "event":
                continue
            mapping = MITRE_MAPPING.get(str(attrs.get("event_type", "")).lower(), {})
            attrs["mitre_tactic"] = mapping.get("mitre_tactic", "Unknown")
            attrs["mitre_technique"] = mapping.get("mitre_technique", "Insufficient evidence")
            attrs["mitre_stage"] = mapping.get("mitre_stage", "Unknown")
        return graph

    def annotate_chains(self, chains: list[dict[str, Any]], graph: nx.DiGraph) -> list[dict[str, Any]]:
        for chain in chains:
            stages: list[str] = []
            for event in chain.get("events", []):
                node_attrs = graph.nodes.get(event["node_id"], {})
                event["mitre_tactic"] = node_attrs.get("mitre_tactic", "Unknown")
                event["mitre_technique"] = node_attrs.get("mitre_technique", "Insufficient evidence")
                event["mitre_stage"] = node_attrs.get("mitre_stage", "Unknown")
                stages.append(event["mitre_stage"])
            chain["mitre_stage"] = sorted({stage for stage in stages if stage != "Unknown"})
        return chains

    def export_mapping(self, graph: nx.DiGraph, output_path: Path) -> None:
        mapping_payload = []
        for node, attrs in graph.nodes(data=True):
            if attrs.get("node_type") != "event":
                continue
            mapping_payload.append(
                {
                    "node_id": node,
                    "event_id": attrs.get("event_id"),
                    "event_type": attrs.get("event_type"),
                    "mitre_tactic": attrs.get("mitre_tactic"),
                    "mitre_technique": attrs.get("mitre_technique"),
                    "mitre_stage": attrs.get("mitre_stage"),
                }
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(mapping_payload, indent=2), encoding="utf-8")
        LOGGER.info("MITRE mapping exported to %s", output_path)
