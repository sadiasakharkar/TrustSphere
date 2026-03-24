"""Feature engineering for offline UEBA anomaly detection."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from tsfresh import extract_features
from tsfresh.feature_extraction import MinimalFCParameters
from tsfresh.utilities.dataframe_functions import impute


LOGGER = logging.getLogger(__name__)


def extract_behavioral_features(
    input_path: str | Path,
    output_path: str | Path,
) -> tuple[pd.DataFrame, Path]:
    """Create row-level and user-level behavior features and persist them."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    frame = pd.read_csv(input_path, parse_dates=["timestamp"])
    if frame.empty:
        raise ValueError("Normalized log dataset is empty.")

    frame = frame.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    frame["total_bytes"] = frame["bytes_sent"] + frame["bytes_received"]
    frame["is_night_activity"] = ((frame["hour"] < 6) | (frame["hour"] >= 21)).astype("int8")
    frame["event_counter"] = frame.groupby("user_id").cumcount() + 1

    user_agg = (
        frame.groupby("user_id", observed=True)
        .agg(
            login_frequency=("login_success", "sum"),
            failed_login_ratio=("failed_attempts", lambda series: float((series > 0).mean())),
            avg_bytes_sent=("bytes_sent", "mean"),
            session_duration_estimate=("timestamp", lambda series: (series.max() - series.min()).total_seconds() / 3600.0),
            unique_ip_count=("ip_address", "nunique"),
            night_activity_ratio=("is_night_activity", "mean"),
        )
        .reset_index()
    )

    frame["rolling_mean_bytes"] = (
        frame.groupby("user_id")["total_bytes"].rolling(window=5, min_periods=1).mean().reset_index(level=0, drop=True)
    )
    frame["rolling_std_bytes"] = (
        frame.groupby("user_id")["total_bytes"].rolling(window=5, min_periods=1).std().reset_index(level=0, drop=True).fillna(0.0)
    )
    previous_timestamp = frame.groupby("user_id")["timestamp"].shift()
    frame["minutes_since_previous"] = (
        (frame["timestamp"] - previous_timestamp).dt.total_seconds().div(60).fillna(0.0)
    )
    frame["event_rate"] = 1.0 / np.maximum(frame["minutes_since_previous"], 1.0)

    tsfresh_input = frame[["user_id", "timestamp_unix", "total_bytes"]].rename(columns={"user_id": "id", "timestamp_unix": "time", "total_bytes": "value"})
    tsfresh_features = extract_features(
        tsfresh_input,
        column_id="id",
        column_sort="time",
        default_fc_parameters=MinimalFCParameters(),
        disable_progressbar=True,
        n_jobs=0,
    )
    tsfresh_features = impute(tsfresh_features)
    tsfresh_features = tsfresh_features.reset_index()
    id_column = tsfresh_features.columns[0]
    tsfresh_features = tsfresh_features.rename(columns={id_column: "user_id"})

    feature_frame = frame.merge(user_agg, on="user_id", how="left").merge(tsfresh_features, on="user_id", how="left")
    feature_frame = feature_frame.fillna(0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    feature_frame.to_csv(output_path, index=False)
    LOGGER.info("Feature dataset saved to %s", output_path)
    return feature_frame, output_path
