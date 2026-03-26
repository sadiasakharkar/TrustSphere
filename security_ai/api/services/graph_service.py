from __future__ import annotations

from typing import Any

import networkx as nx


class GraphService:
    def build_graph(self, incident: dict[str, Any], detections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        detections = detections or []
        graph = nx.DiGraph()
        entities = incident.get("entities") or []
        user = entities[0] if len(entities) > 0 else incident.get("user") or incident.get("entity_id", "unknown-user")
        host = entities[1] if len(entities) > 1 else incident.get("host") or incident.get("entity", "unknown-host")
        ip = entities[2] if len(entities) > 2 else incident.get("ip") or "0.0.0.0"
        process = incident.get("process") or incident.get("process_name") or "powershell.exe"
        database = incident.get("database") or "sensitive-db"

        nodes = [
            (user, {"type": "user", "risk": incident.get("severity", "Medium").lower()}),
            (host, {"type": "host", "risk": "high"}),
            (process, {"type": "process", "risk": "high"}),
            (ip, {"type": "ip", "risk": incident.get("severity", "Medium").lower()}),
            (database, {"type": "database", "risk": "critical" if incident.get("severity") == "Critical" else "high"}),
        ]
        for node_id, attrs in nodes:
            graph.add_node(node_id, **attrs)

        edges = [
            (user, host, "login"),
            (host, process, "execution"),
            (process, ip, "connection"),
            (ip, database, "privilege_change" if incident.get("severity", "").lower() == "critical" else "connection"),
        ]
        for source, target, relation in edges:
            graph.add_edge(source, target, relation=relation)

        path = [user, host, process, ip, database]
        attack_stages = [
            "Initial Access",
            "Credential Access",
            "Privilege Escalation",
            "Lateral Movement",
            "Exfiltration",
        ]
        serialized_nodes = []
        for index, (node_id, attrs) in enumerate(graph.nodes(data=True)):
            serialized_nodes.append({
                "id": f"node-{index}",
                "label": str(node_id),
                "type": attrs.get("type", "entity"),
                "risk": attrs.get("risk", "medium"),
                "x": 15 + (index * 18),
                "y": 30 + ((index % 2) * 18),
            })
        label_to_id = {item["label"]: item["id"] for item in serialized_nodes}
        serialized_edges = []
        for index, (source, target, attrs) in enumerate(graph.edges(data=True)):
            serialized_edges.append({
                "id": f"edge-{index}",
                "from": label_to_id[str(source)],
                "to": label_to_id[str(target)],
                "label": attrs.get("relation", "connection"),
            })

        return {
            "incident_id": incident.get("id"),
            "nodes": serialized_nodes,
            "edges": serialized_edges,
            "riskLevels": [node["risk"] for node in serialized_nodes],
            "attack_chain": path,
            "attack_stages": attack_stages,
            "chain_summary": " → ".join(path),
            "detections": detections,
        }
