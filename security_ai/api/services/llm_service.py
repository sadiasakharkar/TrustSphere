from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from typing import Any

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"
if str(TRUSTSPHERE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(TRUSTSPHERE_AI_DIR))

from src.llm.ollama_client import LocalLLM


class LLMService:
    def __init__(self) -> None:
        self.client = LocalLLM()

    def summarize_incident(self, *, anomaly_result: dict[str, Any], attack_graph: dict[str, Any], entity_behavior: dict[str, Any], historical_context: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_prompt(anomaly_result, attack_graph, entity_behavior, historical_context)
        try:
            raw = self.client.generate(prompt)
            parsed = self._extract_json(raw)
            return self._validate(parsed)
        except Exception as exc:
            LOGGER.warning("LLM reasoning unavailable, using deterministic fallback: %s", exc)
            return self._fallback(anomaly_result, attack_graph, entity_behavior)

    def _build_prompt(self, anomaly_result: dict[str, Any], attack_graph: dict[str, Any], entity_behavior: dict[str, Any], historical_context: dict[str, Any]) -> str:
        return (
            "Return ONLY valid JSON with keys summary, reasoning, attack_stage, confidence, recommended_actions.\n"
            f"anomaly_result={json.dumps(anomaly_result, default=str)}\n"
            f"attack_graph={json.dumps(attack_graph, default=str)}\n"
            f"entity_behavior={json.dumps(entity_behavior, default=str)}\n"
            f"historical_context={json.dumps(historical_context, default=str)}"
        )

    def _extract_json(self, raw: str) -> dict[str, Any]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in LLM response")
        return json.loads(raw[start:end + 1])

    def _validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = {"summary", "reasoning", "attack_stage", "confidence", "recommended_actions"}
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"Missing LLM JSON keys: {sorted(missing)}")
        if not isinstance(payload.get("recommended_actions"), list):
            raise ValueError("recommended_actions must be a list")
        payload["confidence"] = float(payload.get("confidence", 0.0))
        return payload

    def _fallback(self, anomaly_result: dict[str, Any], attack_graph: dict[str, Any], entity_behavior: dict[str, Any]) -> dict[str, Any]:
        severity_hint = str(entity_behavior.get("severity") or entity_behavior.get("risk_score") or "high")
        return {
            "summary": f"TrustSphere correlated anomalous entity behavior into an active {severity_hint.lower()}-risk incident chain.",
            "reasoning": f"Anomaly score {anomaly_result.get('anomaly_score', 0.0)} combined with graph path {attack_graph.get('chain_summary', 'not available')} raised the final SOC risk.",
            "attack_stage": (attack_graph.get("attack_stages") or ["Initial Access"])[-1],
            "confidence": 0.92,
            "recommended_actions": [
                "Validate the impacted account and host against approved activity.",
                "Contain the affected endpoint or identity if the behavior is not authorized.",
                "Preserve graph and timeline evidence for incident response.",
            ],
        }
