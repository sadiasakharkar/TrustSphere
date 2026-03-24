"""UEBA risk scoring engine for TrustSphere."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


class UEBARiskEngine:
    """Convert model outputs into SOC-facing UEBA risk intelligence."""

    def __init__(self, anomaly_weight: float = 0.4, behavior_weight: float = 0.3, historical_weight: float = 0.3) -> None:
        total = anomaly_weight + behavior_weight + historical_weight
        if total <= 0:
            raise ValueError("Risk weights must sum to a positive value.")
        self.anomaly_weight = anomaly_weight / total
        self.behavior_weight = behavior_weight / total
        self.historical_weight = historical_weight / total

    def evaluate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"entity_id", "timestamp", "anomaly_score"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing required columns for risk engine: {sorted(missing)}")

        frame = df.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).sort_values(["entity_id", "timestamp"]).reset_index(drop=True)
        if "behavioral_risk" not in frame.columns:
            frame["behavioral_risk"] = self._derive_behavioral_risk(frame)
        if "historical_risk" not in frame.columns:
            frame["historical_risk"] = self._derive_historical_risk(frame)

        frame["risk_score"] = (
            100.0
            * (
                self.anomaly_weight * frame["anomaly_score"].clip(0.0, 1.0)
                + self.behavior_weight * frame["behavioral_risk"].clip(0.0, 1.0)
                + self.historical_weight * frame["historical_risk"].clip(0.0, 1.0)
            )
        ).round(2)
        frame["risk_level"] = frame["risk_score"].apply(self.assign_risk_level)
        return frame[[
            "entity_id",
            "timestamp",
            "anomaly_score",
            "risk_score",
            "risk_level",
            "behavioral_risk",
            "historical_risk",
        ] + [column for column in frame.columns if column not in {"entity_id", "timestamp", "anomaly_score", "risk_score", "risk_level", "behavioral_risk", "historical_risk"}]]

    def assign_risk_level(self, risk_score: float) -> str:
        if risk_score < 30:
            return "Low"
        if risk_score < 70:
            return "Medium"
        return "Critical"

    def save_scores(self, df: pd.DataFrame, output_path: str | Path) -> Path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(destination, index=False)
        except Exception as exc:
            if _strict_production_mode():
                raise RuntimeError(f"Parquet export failed for {destination} in production mode.") from exc
            fallback = destination.with_suffix(".csv")
            df.to_csv(fallback, index=False)
            LOGGER.warning("Parquet export failed for %s (%s). Wrote CSV fallback to %s", destination, exc, fallback)
        return destination

    def _derive_behavioral_risk(self, frame: pd.DataFrame) -> pd.Series:
        proxies = []
        status_series = frame.get("status", pd.Series(["unknown"] * len(frame))).astype(str).str.lower()
        event_series = frame.get("event_type", pd.Series(["unknown"] * len(frame))).astype(str).str.lower()
        failed_attempts = pd.to_numeric(frame.get("failed_attempts", 0), errors="coerce").fillna(0.0)
        bytes_sent = pd.to_numeric(frame.get("bytes_sent", 0), errors="coerce").fillna(0.0)
        threshold = float(bytes_sent.quantile(0.95)) if len(bytes_sent) else 0.0
        for idx in range(len(frame)):
            value = 0.0
            if status_series.iloc[idx] in {"fail", "failed", "error", "denied"}:
                value += 0.4
            if failed_attempts.iloc[idx] > 5:
                value += 0.3
            if "privilege" in event_series.iloc[idx] or "admin_action" in event_series.iloc[idx]:
                value += 0.2
            if bytes_sent.iloc[idx] >= threshold and threshold > 0:
                value += 0.1
            proxies.append(min(value, 1.0))
        return pd.Series(proxies, index=frame.index, dtype=float)

    def _derive_historical_risk(self, frame: pd.DataFrame) -> pd.Series:
        cumulative = frame.groupby("entity_id").cumcount().astype(float)
        if len(cumulative) == 0 or float(cumulative.max()) == float(cumulative.min()):
            return pd.Series(np.zeros(len(frame)), index=frame.index, dtype=float)
        normalized = (cumulative - cumulative.min()) / (cumulative.max() - cumulative.min())
        return normalized.astype(float)


def _strict_production_mode() -> bool:
    return os.getenv("TRUSTSPHERE_ENV", "development").strip().lower() in {"prod", "production"}
