"""Guard pipeline for blocking prompt injection before LLM execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from security_ai.features.prompt_guard_features import PromptGuardFeatureEngineer
from security_ai.models.prompt_guard import PromptRuleEngine

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "artifacts" / "prompt_guard_model"
RULES_PATH = BASE_DIR / "artifacts" / "rules.json"


class PromptInjectionGuard:
    """User input -> detector -> block or allow."""

    def __init__(self) -> None:
        self.model = joblib.load(MODEL_DIR / "model.joblib")
        self.rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        self.rule_engine = PromptRuleEngine(self.rules)
        self.feature_engineer = PromptGuardFeatureEngineer()

    def evaluate(self, prompt: str) -> dict:
        rule_result = self.rule_engine.evaluate(prompt)
        dataset = self.feature_engineer.build_dataset([{"prompt": prompt, "label": 0}])
        artifacts = self.feature_engineer.build_features(dataset)
        probability = float(self.model.predict_proba(artifacts.dataframe)[:, 1][0])
        blocked = rule_result["block"] or probability >= 0.5
        return {
            "blocked": blocked,
            "label": "INJECTION" if blocked else "SAFE",
            "injection_probability": probability,
            "matched_rules": rule_result["matched_rules"],
            "action": "block" if blocked else "send_to_llm",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    print(json.dumps(PromptInjectionGuard().evaluate(args.prompt), indent=2))
