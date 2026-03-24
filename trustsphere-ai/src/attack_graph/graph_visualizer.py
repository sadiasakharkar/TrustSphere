"""Frontend-ready attack graph export helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

LOGGER = logging.getLogger(__name__)


class GraphVisualizer:
    """Convert NetworkX graphs into D3-compatible JSON payloads."""

    def export_graph(self, graph: nx.DiGraph, output_path: Path) -> dict[str, list[dict[str, Any]]]:
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            payload = {"id": node_id}
            payload.update(attrs)
            nodes.append(payload)

        edges = []
        for source, target, attrs in graph.edges(data=True):
            payload = {"source": source, "target": target}
            payload.update(attrs)
            edges.append(payload)

        export_payload = {"nodes": nodes, "edges": edges}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
        LOGGER.info("Graph exported to %s", output_path)
        return export_payload
