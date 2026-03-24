"""Normalization pipeline for offline TrustSphere logs."""

from __future__ import annotations

import logging
from pathlib import Path
import socket
import struct

import pandas as pd


LOGGER = logging.getLogger(__name__)


def normalize_logs(input_path: str | Path, output_path: str | Path) -> Path:
    """Normalize raw logs into a model-ready CSV file."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Raw log file not found: {input_path}")

    frame = pd.read_csv(input_path)
    frame.columns = [column.strip().lower() for column in frame.columns]

    expected_columns = [
        "timestamp",
        "user_id",
        "ip_address",
        "event_type",
        "bytes_sent",
        "bytes_received",
        "login_success",
        "device_type",
        "location",
        "process_name",
        "failed_attempts",
    ]
    missing_columns = [column for column in expected_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Missing required log columns: {missing_columns}")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "user_id"]).copy()
    frame["user_id"] = frame["user_id"].astype(str).str.strip().str.lower()

    numeric_defaults = {
        "bytes_sent": 0,
        "bytes_received": 0,
        "login_success": 0,
        "failed_attempts": 0,
    }
    for column, default_value in numeric_defaults.items():
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(default_value)

    for column in ["event_type", "device_type", "location", "process_name", "ip_address"]:
        frame[column] = frame[column].fillna("unknown").astype(str).str.strip().str.lower()

    frame["timestamp_unix"] = (frame["timestamp"].astype("int64") // 10**9).astype("int64")
    frame["hour"] = frame["timestamp"].dt.hour.astype("int16")
    frame["day_of_week"] = frame["timestamp"].dt.dayofweek.astype("int8")
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype("int8")
    frame["ip_numeric"] = frame["ip_address"].map(_ip_to_int).astype("int64")

    for column in ["event_type", "device_type", "location", "process_name", "user_id"]:
        frame[f"{column}_encoded"] = pd.factorize(frame[column], sort=True)[0].astype("int32")

    frame = frame.sort_values(["timestamp", "user_id"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("Normalized logs saved to %s", output_path)
    return output_path


def _ip_to_int(ip_value: str) -> int:
    try:
        return struct.unpack("!I", socket.inet_aton(ip_value))[0]
    except OSError:
        return 0
