"""Feature engineering for credential exposure detection."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
JWT_PATTERN = re.compile(r"eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+")
PASSWORD_PATTERN = re.compile(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}")
API_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|token|secret)[\s:=\"']+([A-Za-z0-9_\-]{12,})")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
EMAIL_PASSWORD_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\s*[:|,;]\s*[^\s]{8,}")
GENERIC_TOKEN_PATTERN = re.compile(r"(?i)(bearer\s+[A-Za-z0-9\-_.=]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})")

CONTEXT_VERBS = {"commit", "push", "paste", "share", "upload", "store", "hardcode", "expose", "copy"}
COMMIT_SIGNALS = {"temporary", "hotfix", "debug", "credentials", "token", "secret", "env", "config"}
PASTE_SIGNALS = {"here is", "pasted", "snippet", "stack trace", "env file", "configuration"}


@dataclass(slots=True)
class CredentialDetectionArtifacts:
    dataframe: pd.DataFrame
    feature_columns: list[str]


class CredentialFeatureEngineer:
    """Build regex and context features for credential exposure detection."""

    def build_dataset(self, rows: list[dict[str, Any]] | None = None) -> pd.DataFrame:
        if rows:
            frame = pd.DataFrame(rows)
        else:
            frame = self._mock_dataset()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if "text" not in frame.columns:
            raise ValueError("Credential detector input must contain a text column.")
        if "label" not in frame.columns:
            frame["label"] = 0
        frame["commit_message"] = frame.get("commit_message", "")
        frame["paste_context"] = frame.get("paste_context", "")
        return frame

    def build_features(self, frame: pd.DataFrame) -> CredentialDetectionArtifacts:
        dataset = frame.copy()
        dataset["aws_key_matches"] = dataset["text"].astype(str).map(lambda value: len(AWS_KEY_PATTERN.findall(value)))
        dataset["jwt_matches"] = dataset["text"].astype(str).map(lambda value: len(JWT_PATTERN.findall(value)))
        dataset["password_matches"] = dataset["text"].astype(str).map(lambda value: len(PASSWORD_PATTERN.findall(value)))
        dataset["api_key_matches"] = dataset["text"].astype(str).map(lambda value: len(API_KEY_PATTERN.findall(value)))
        dataset["private_key_matches"] = dataset["text"].astype(str).map(lambda value: len(PRIVATE_KEY_PATTERN.findall(value)))
        dataset["email_password_combo_matches"] = dataset["text"].astype(str).map(lambda value: len(EMAIL_PASSWORD_PATTERN.findall(value)))
        dataset["generic_token_matches"] = dataset["text"].astype(str).map(lambda value: len(GENERIC_TOKEN_PATTERN.findall(value)))
        dataset["surrounding_verb_score"] = dataset["text"].astype(str).map(lambda value: self._keyword_score(value, CONTEXT_VERBS))
        dataset["commit_signal_score"] = dataset["commit_message"].astype(str).map(lambda value: self._keyword_score(value, COMMIT_SIGNALS))
        dataset["paste_context_score"] = dataset["paste_context"].astype(str).map(lambda value: self._keyword_score(value, PASTE_SIGNALS))
        dataset["context_risk"] = (
            0.5 * dataset["surrounding_verb_score"]
            + 0.3 * dataset["commit_signal_score"]
            + 0.2 * dataset["paste_context_score"]
        )
        dataset["regex_match_weight"] = (
            1.0 * dataset["aws_key_matches"]
            + 0.8 * dataset["jwt_matches"]
            + 0.6 * dataset["api_key_matches"]
            + 1.2 * dataset["private_key_matches"]
            + 0.9 * dataset["email_password_combo_matches"]
            + 0.5 * dataset["password_matches"]
            + 0.7 * dataset["generic_token_matches"]
        )
        feature_columns = [
            "aws_key_matches",
            "jwt_matches",
            "password_matches",
            "api_key_matches",
            "private_key_matches",
            "email_password_combo_matches",
            "generic_token_matches",
            "surrounding_verb_score",
            "commit_signal_score",
            "paste_context_score",
            "context_risk",
            "regex_match_weight",
        ]
        return CredentialDetectionArtifacts(dataframe=dataset, feature_columns=feature_columns)

    def export_rules(self, output_path: str | Path) -> Path:
        payload = {
            "aws": AWS_KEY_PATTERN.pattern,
            "jwt": JWT_PATTERN.pattern,
            "password": PASSWORD_PATTERN.pattern,
            "api_key": API_KEY_PATTERN.pattern,
            "private_key": PRIVATE_KEY_PATTERN.pattern,
            "email_password_combo": EMAIL_PASSWORD_PATTERN.pattern,
            "generic_token": GENERIC_TOKEN_PATTERN.pattern,
        }
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        yaml_text = "\n".join(f"{key}: {json.dumps(value)}" for key, value in payload.items()) + "\n"
        path.write_text(yaml_text, encoding="utf-8")
        return path

    def _keyword_score(self, text: str, vocabulary: set[str]) -> float:
        lowered = str(text).lower()
        return float(sum(lowered.count(term) for term in vocabulary))

    def _mock_dataset(self) -> pd.DataFrame:
        rows = [
            {"text": "export AWS_KEY=AKIA1234567890ABCDEF and push later", "commit_message": "temp debug credentials", "paste_context": "env file", "label": 1},
            {"text": "meeting notes for project sync tomorrow", "commit_message": "docs update", "paste_context": "notes", "label": 0},
            {"text": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature", "commit_message": "api hotfix token", "paste_context": "stack trace", "label": 1},
            {"text": "customer email thread with no sensitive values", "commit_message": "email import", "paste_context": "support", "label": 0},
            {"text": "-----BEGIN PRIVATE KEY----- hidden material", "commit_message": "config copy", "paste_context": "pasted key", "label": 1},
            {"text": "jane@example.com:Password123", "commit_message": "migration data", "paste_context": "bulk paste", "label": 1},
        ]
        return pd.DataFrame(rows)
