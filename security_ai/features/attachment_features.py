"""Feature engineering for malicious attachment detection."""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

RISKY_EXTENSIONS = {"exe", "scr", "js", "jar", "vbs", "ps1", "xlsm", "docm", "hta", "bat"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"}
ARCHIVE_EXTENSIONS = {"zip", "rar", "7z", "iso"}
EXECUTION_HINTS = {"download", "spawned", "executed", "launched", "opened"}
PRIV_ESC_HINTS = {"elevated", "admin", "uac", "privilege", "sudo", "runas"}
MACRO_HINTS = {"vba", "macro", "autoopen", "document_open", "xlm"}


@dataclass(slots=True)
class AttachmentFeatureArtifacts:
    dataframe: pd.DataFrame
    feature_columns: list[str]


class AttachmentFeatureEngineer:
    """Build metadata and behavioral features for attachment risk scoring."""

    def build_dataset(self, rows: list[dict[str, Any]] | None = None) -> pd.DataFrame:
        frame = pd.DataFrame(rows) if rows else self._mock_dataset()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if "filename" not in frame.columns:
            raise ValueError("Attachment dataset requires a filename column.")
        if "label" not in frame.columns:
            frame["label"] = 0
        frame["size_bytes"] = pd.to_numeric(frame.get("size_bytes", 0), errors="coerce").fillna(0)
        frame["content_text"] = frame.get("content_text", "")
        frame["event_context"] = frame.get("event_context", "")
        frame["post_download_action"] = frame.get("post_download_action", "")
        return frame

    def build_features(self, frame: pd.DataFrame) -> AttachmentFeatureArtifacts:
        dataset = frame.copy()
        dataset["extension"] = dataset["filename"].astype(str).map(self._extension)
        dataset["entropy"] = dataset["content_text"].astype(str).map(self._entropy)
        dataset["size_kb"] = dataset["size_bytes"] / 1024.0
        dataset["size_anomaly"] = dataset["size_bytes"].map(self._size_anomaly)
        dataset["risky_extension"] = dataset["extension"].isin(RISKY_EXTENSIONS).astype(int)
        dataset["document_extension"] = dataset["extension"].isin(DOCUMENT_EXTENSIONS).astype(int)
        dataset["archive_extension"] = dataset["extension"].isin(ARCHIVE_EXTENSIONS).astype(int)
        dataset["extension_mismatch"] = dataset.apply(self._extension_mismatch, axis=1)
        dataset["macro_presence"] = dataset["content_text"].astype(str).str.lower().map(lambda text: int(any(token in text for token in MACRO_HINTS)))
        dataset["execution_after_download"] = dataset["post_download_action"].astype(str).str.lower().map(lambda text: int(any(token in text for token in EXECUTION_HINTS)))
        dataset["privilege_escalation_behavior"] = dataset["event_context"].astype(str).str.lower().map(lambda text: int(any(token in text for token in PRIV_ESC_HINTS)))
        dataset["double_extension"] = dataset["filename"].astype(str).str.lower().str.contains(r"\.[a-z0-9]{1,5}\.[a-z0-9]{1,5}$", regex=True).astype(int)
        dataset["embedded_script_hint"] = dataset["content_text"].astype(str).str.lower().str.contains(r"powershell|cmd\.exe|wscript|shell", regex=True).astype(int)
        dataset["suspicious_keyword_density"] = dataset["content_text"].astype(str).str.lower().map(self._keyword_density)
        feature_columns = [
            "entropy",
            "size_kb",
            "size_anomaly",
            "risky_extension",
            "document_extension",
            "archive_extension",
            "extension_mismatch",
            "macro_presence",
            "execution_after_download",
            "privilege_escalation_behavior",
            "double_extension",
            "embedded_script_hint",
            "suspicious_keyword_density",
        ]
        return AttachmentFeatureArtifacts(dataframe=dataset, feature_columns=feature_columns)

    def _extension(self, filename: str) -> str:
        parts = str(filename).lower().rsplit(".", 1)
        return parts[-1] if len(parts) == 2 else ""

    def _entropy(self, text: str) -> float:
        chars = list(str(text))
        if not chars:
            return 0.0
        probabilities = pd.Series(chars).value_counts(normalize=True)
        return float(-(probabilities * np.log2(probabilities + 1e-12)).sum())

    def _size_anomaly(self, size_bytes: float) -> float:
        if size_bytes <= 0:
            return 0.0
        if size_bytes < 2048:
            return 0.7
        if size_bytes > 15 * 1024 * 1024:
            return 0.8
        if 50 * 1024 <= size_bytes <= 8 * 1024 * 1024:
            return 0.1
        return 0.4

    def _extension_mismatch(self, row: pd.Series) -> int:
        extension = row.get("extension", "")
        content = str(row.get("content_text", "")).lower()
        if extension in DOCUMENT_EXTENSIONS and any(token in content for token in {"mz", "powershell", "wscript", "cmd.exe"}):
            return 1
        if extension in {"pdf", "docx", "xlsx"} and any(token in content for token in MACRO_HINTS):
            return 1
        return 0

    def _keyword_density(self, text: str) -> float:
        lowered = str(text).lower()
        tokens = re.findall(r"[a-z0-9_.-]+", lowered)
        suspicious = sum(token in MACRO_HINTS or token in EXECUTION_HINTS or token in PRIV_ESC_HINTS for token in tokens)
        return suspicious / max(len(tokens), 1)

    def _mock_dataset(self) -> pd.DataFrame:
        rows = [
            {"filename": "invoice.pdf", "size_bytes": 120000, "content_text": "invoice details attached", "event_context": "download completed", "post_download_action": "opened in reader", "label": 0},
            {"filename": "invoice.pdf.exe", "size_bytes": 98000, "content_text": "MZ powershell cmd.exe payload", "event_context": "elevated admin prompt", "post_download_action": "download spawned and executed", "label": 1},
            {"filename": "report.xlsm", "size_bytes": 250000, "content_text": "macro autoopen vba document_open", "event_context": "user downloaded attachment", "post_download_action": "opened and launched", "label": 1},
            {"filename": "presentation.pptx", "size_bytes": 3300000, "content_text": "quarterly review presentation", "event_context": "opened in office", "post_download_action": "opened", "label": 0},
            {"filename": "archive.zip", "size_bytes": 500000, "content_text": "compressed project files", "event_context": "download completed", "post_download_action": "saved", "label": 0},
            {"filename": "payload.js", "size_bytes": 800, "content_text": "wscript shell runas sudo", "event_context": "download led to privilege escalation", "post_download_action": "executed after download", "label": 1},
        ]
        return pd.DataFrame(rows)
