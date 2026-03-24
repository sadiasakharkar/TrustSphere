"""Context compression for TrustSphere SOC LLM reasoning."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


class SOCContextBuilder:
    """Build concise attack intelligence context for local LLM inference."""

    def __init__(self, outputs_dir: str | Path, max_characters: int = 6000) -> None:
        self.outputs_dir = Path(outputs_dir)
        self.max_characters = max_characters

    def build_context(self) -> dict[str, Any]:
        attack_paths = self._load_json(self.outputs_dir / "attack_paths.json", default=self._sample_payload()["attack_paths"])
        risk_scores = self._load_json(self.outputs_dir / "graph_risk_scores.json", default=self._sample_payload()["graph_risk_scores"])
        mitre_mapping = self._load_json(self.outputs_dir / "mitre_mapping.json", default=self._sample_payload()["mitre_mapping"])

        context = {
            "threat_summary": self._build_threat_summary(attack_paths, risk_scores),
            "affected_users": self._extract_affected_users(attack_paths),
            "attack_timeline": self._build_timeline(attack_paths),
            "risk_levels": self._extract_risk_levels(risk_scores),
            "mitre_stages": self._extract_mitre_stages(mitre_mapping),
            "key_evidence": self._extract_key_evidence(attack_paths, risk_scores),
        }
        context_text = json.dumps(context, indent=2)
        if len(context_text) > self.max_characters:
            context["attack_timeline"] = context["attack_timeline"][:8]
            context["key_evidence"] = context["key_evidence"][:8]
            context["mitre_stages"] = context["mitre_stages"][:10]
            context_text = json.dumps(context, indent=2)[: self.max_characters]
        context["context_text"] = context_text
        return context

    def _build_threat_summary(self, attack_paths: list[dict[str, Any]], risk_scores: dict[str, Any]) -> dict[str, Any]:
        top_chain = next(iter(risk_scores.get("chain_scores", [])), {})
        return {
            "detected_chains": len(attack_paths),
            "highest_severity": top_chain.get("severity_level", "LOW"),
            "highest_severity_score": top_chain.get("severity_score", 0.0),
            "critical_chains": risk_scores.get("critical_chains", 0),
        }

    def _extract_affected_users(self, attack_paths: list[dict[str, Any]]) -> list[str]:
        users = []
        for chain in attack_paths[:10]:
            for event in chain.get("events", []):
                user = event.get("user")
                if user and user not in users:
                    users.append(user)
        return users

    def _build_timeline(self, attack_paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = []
        for chain in attack_paths[:6]:
            for event in chain.get("events", [])[:6]:
                timeline.append(
                    {
                        "timestamp": event.get("timestamp"),
                        "event_type": event.get("event_type"),
                        "user": event.get("user"),
                        "host": event.get("host"),
                        "risk_level": event.get("risk_level"),
                        "mitre_stage": event.get("mitre_stage", "Unknown"),
                    }
                )
        timeline.sort(key=lambda item: str(item.get("timestamp", "")))
        return timeline

    def _extract_risk_levels(self, risk_scores: dict[str, Any]) -> dict[str, Any]:
        return {
            "critical_chains": risk_scores.get("critical_chains", 0),
            "top_chain_levels": [chain.get("severity_level", "LOW") for chain in risk_scores.get("chain_scores", [])[:5]],
            "top_node_risks": risk_scores.get("node_scores", [])[:10],
        }

    def _extract_mitre_stages(self, mitre_mapping: list[dict[str, Any]]) -> list[str]:
        stages = []
        for item in mitre_mapping:
            stage = item.get("mitre_stage")
            if stage and stage not in stages:
                stages.append(stage)
        return stages

    def _extract_key_evidence(self, attack_paths: list[dict[str, Any]], risk_scores: dict[str, Any]) -> list[str]:
        evidence = []
        for chain in attack_paths[:5]:
            evidence.extend(chain.get("risk_reason", [])[:3])
            evidence.extend(chain.get("why_linked", [])[:3])
        for node in risk_scores.get("node_scores", [])[:5]:
            evidence.append(
                f"{node.get('event_type', 'unknown_event')} on {node.get('event_id', 'unknown')} scored {node.get('node_risk', 0)} risk"
            )
        deduped = []
        for item in evidence:
            if item and item not in deduped:
                deduped.append(item)
        return deduped

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        LOGGER.warning("Missing %s, using bundled sample attack intelligence", path)
        return default

    def _sample_payload(self) -> dict[str, Any]:
        sample_path = Path(__file__).resolve().with_name("sample_attack.json")
        return json.loads(sample_path.read_text(encoding="utf-8"))
