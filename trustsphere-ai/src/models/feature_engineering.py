"""Advanced UEBA feature engineering for TrustSphere."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import numpy as np
import pandas as pd

try:
    from .config import DEVICE_WINDOW_DAYS, FEATURE_WINDOW_HOURS, SHORT_WINDOW_HOURS, TSFRESH_ENABLED
except ImportError:
    from config import DEVICE_WINDOW_DAYS, FEATURE_WINDOW_HOURS, SHORT_WINDOW_HOURS, TSFRESH_ENABLED


LOGGER = logging.getLogger(__name__)

try:
    from tsfresh import extract_features
    from tsfresh.feature_extraction import MinimalFCParameters
    from tsfresh.utilities.dataframe_functions import impute

    TSFRESH_AVAILABLE = True
except Exception:
    TSFRESH_AVAILABLE = False


@dataclass(slots=True)
class FeatureEngineeringResult:
    """Container for engineered features and metadata."""

    features_df: pd.DataFrame
    metadata_df: pd.DataFrame
    feature_columns: list[str]


class BehavioralFeatureEngineer:
    """Create advanced behavioral features from normalized CERT-style event data."""

    def __init__(
        self,
        feature_window_hours: int = FEATURE_WINDOW_HOURS,
        short_window_hours: int = SHORT_WINDOW_HOURS,
        device_window_days: int = DEVICE_WINDOW_DAYS,
        tsfresh_enabled: bool = TSFRESH_ENABLED,
    ) -> None:
        self.feature_window_hours = feature_window_hours
        self.short_window_hours = short_window_hours
        self.device_window_days = device_window_days
        self.tsfresh_enabled = tsfresh_enabled and TSFRESH_AVAILABLE
        self.feature_columns_: list[str] = []

    def fit_transform(self, dataframe: pd.DataFrame) -> FeatureEngineeringResult:
        """Fit-free transform API for training pipelines."""
        result = self.transform(dataframe)
        self.feature_columns_ = result.feature_columns
        return result

    def transform(self, dataframe: pd.DataFrame) -> FeatureEngineeringResult:
        """Transform normalized logs into numeric UEBA features."""
        frame = self._prepare_dataframe(dataframe)
        engineered = self._build_core_features(frame)
        if self.tsfresh_enabled:
            engineered = self._append_tsfresh_features(frame, engineered)
        engineered = self._sanitize_numeric_frame(engineered)

        metadata_columns = ["timestamp", "user", "host", "event_type", "status"]
        metadata_df = engineered[metadata_columns].copy()
        numeric_columns = [
            column
            for column in engineered.columns
            if column not in metadata_columns and pd.api.types.is_numeric_dtype(engineered[column])
        ]
        features_df = engineered[numeric_columns].copy()
        LOGGER.info("Engineered %s rows with %s numeric features", len(features_df), len(numeric_columns))
        return FeatureEngineeringResult(
            features_df=features_df,
            metadata_df=metadata_df,
            feature_columns=numeric_columns,
        )

    def _prepare_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        frame = dataframe.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        for column in ["timestamp", "user", "host", "event_type", "status"]:
            if column not in frame.columns:
                raise ValueError(f"Missing required normalized column: {column}")

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "user", "host", "event_type", "status"]).copy()
        frame["user"] = frame["user"].astype(str).str.strip().str.lower()
        frame["host"] = frame["host"].astype(str).str.strip().str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.strip().str.lower()
        frame["status"] = frame["status"].astype(str).str.strip().str.lower()
        frame = frame.sort_values(["user", "timestamp"]).reset_index(drop=True)
        frame["row_id"] = np.arange(len(frame), dtype=np.int64)
        frame["login_hour"] = frame["timestamp"].dt.hour.astype(np.int16)
        frame["day_of_week"] = frame["timestamp"].dt.dayofweek.astype(np.int8)
        frame["weekend_flag"] = (frame["day_of_week"] >= 5).astype(np.int8)
        frame["is_failed"] = frame["status"].isin(["fail", "failed", "denied", "error"]).astype(np.int8)
        frame["is_login"] = frame["event_type"].str.contains("logon|login", regex=True).astype(np.int8)
        frame["night_flag"] = ((frame["login_hour"] < 6) | (frame["login_hour"] >= 21)).astype(np.int8)
        frame["prev_timestamp"] = frame.groupby("user")["timestamp"].shift()
        frame["mean_activity_interval"] = (
            (frame["timestamp"] - frame["prev_timestamp"]).dt.total_seconds().div(60).fillna(0.0)
        )
        return frame

    def _build_core_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        per_user = frame.groupby("user", group_keys=False, sort=False)
        engineered = frame.copy()

        engineered["night_activity_ratio"] = per_user["night_flag"].transform("mean")
        engineered["failed_login_ratio"] = per_user["is_failed"].transform("mean")
        engineered["session_density"] = per_user["timestamp"].transform(self._session_density)
        engineered["event_entropy"] = per_user["event_type"].transform(self._event_entropy)
        engineered["activity_switch_rate"] = per_user["event_type"].transform(self._activity_switch_rate)
        engineered["burstiness_score"] = per_user["mean_activity_interval"].transform(self._burstiness_score)
        engineered["std_session_duration"] = per_user["mean_activity_interval"].transform("std").fillna(0.0)

        engineered["logins_last_1h"] = self._rolling_login_count(engineered, hours=self.short_window_hours)
        engineered["logins_last_24h"] = self._rolling_login_count(engineered, hours=self.feature_window_hours)
        engineered["unique_devices_7d"] = self._rolling_unique_hosts(engineered, days=self.device_window_days)
        engineered["new_device_flag"] = self._new_device_flag(engineered)
        engineered["device_change_rate"] = self._device_change_rate(engineered)

        return engineered

    def _append_tsfresh_features(self, frame: pd.DataFrame, engineered: pd.DataFrame) -> pd.DataFrame:
        tsfresh_source = frame[["row_id", "timestamp", "login_hour", "is_failed"]].copy()
        tsfresh_source["time_sort"] = (tsfresh_source["timestamp"].astype("int64") // 10**9).astype("int64")
        long_frame = pd.concat(
            [
                tsfresh_source[["row_id", "time_sort", "login_hour"]].rename(columns={"login_hour": "value"}).assign(kind="login_hour"),
                tsfresh_source[["row_id", "time_sort", "is_failed"]].rename(columns={"is_failed": "value"}).assign(kind="is_failed"),
            ],
            ignore_index=True,
        )
        extracted = extract_features(
            long_frame,
            column_id="row_id",
            column_sort="time_sort",
            column_kind="kind",
            column_value="value",
            default_fc_parameters=MinimalFCParameters(),
            disable_progressbar=True,
            n_jobs=0,
        )
        extracted = impute(extracted)
        extracted = extracted.reset_index()
        extracted = extracted.rename(columns={extracted.columns[0]: "row_id"})
        extracted = self._drop_highly_correlated(extracted, threshold=0.98)
        merged = engineered.merge(extracted, on="row_id", how="left")
        return merged

    def _sanitize_numeric_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric_columns = frame.select_dtypes(include=["number", "bool"]).columns
        frame[numeric_columns] = frame[numeric_columns].replace([np.inf, -np.inf], np.nan)
        frame[numeric_columns] = frame[numeric_columns].fillna(0.0)
        return frame

    def _rolling_login_count(self, frame: pd.DataFrame, hours: int) -> pd.Series:
        outputs: list[pd.Series] = []
        for _, user_frame in frame.groupby("user", sort=False):
            indexed = user_frame.set_index("timestamp")
            values = (
                indexed["is_login"]
                .rolling(f"{hours}h", min_periods=1)
                .sum()
                .reset_index(drop=True)
            )
            outputs.append(pd.Series(values.to_numpy(), index=user_frame.index))
        return pd.concat(outputs).sort_index().astype(np.float32)

    def _rolling_unique_hosts(self, frame: pd.DataFrame, days: int) -> pd.Series:
        outputs: list[pd.Series] = []
        window_delta = pd.Timedelta(days=days)
        for _, user_frame in frame.groupby("user", sort=False):
            host_counts = []
            timestamps = user_frame["timestamp"].to_numpy()
            hosts = user_frame["host"].tolist()
            for idx, current_time in enumerate(timestamps):
                lower_bound = pd.Timestamp(current_time) - window_delta
                start = 0
                while start < idx and pd.Timestamp(timestamps[start]) < lower_bound:
                    start += 1
                host_counts.append(len(set(hosts[start : idx + 1])))
            outputs.append(pd.Series(host_counts, index=user_frame.index))
        return pd.concat(outputs).sort_index().astype(np.float32)

    def _new_device_flag(self, frame: pd.DataFrame) -> pd.Series:
        outputs: list[pd.Series] = []
        for _, user_frame in frame.groupby("user", sort=False):
            seen_hosts: set[str] = set()
            flags: list[int] = []
            for host in user_frame["host"]:
                host_value = str(host)
                flags.append(0 if host_value in seen_hosts else 1)
                seen_hosts.add(host_value)
            outputs.append(pd.Series(flags, index=user_frame.index))
        return pd.concat(outputs).sort_index().astype(np.int8)

    def _device_change_rate(self, frame: pd.DataFrame) -> pd.Series:
        outputs: list[pd.Series] = []
        for _, user_frame in frame.groupby("user", sort=False):
            previous_hosts = user_frame["host"].shift()
            switches = (previous_hosts.notna() & (previous_hosts != user_frame["host"])).astype(np.int8)
            cumulative_switches = switches.cumsum()
            positions = np.arange(1, len(user_frame) + 1)
            rates = cumulative_switches / np.maximum(positions - 1, 1)
            outputs.append(pd.Series(rates.to_numpy(), index=user_frame.index))
        return pd.concat(outputs).sort_index().astype(np.float32)

    def _session_density(self, series: pd.Series) -> pd.Series:
        if len(series) <= 1:
            return pd.Series(np.zeros(len(series)), index=series.index)
        duration_hours = max((series.max() - series.min()).total_seconds() / 3600.0, 1.0)
        density = len(series) / duration_hours
        return pd.Series(np.repeat(density, len(series)), index=series.index)

    def _event_entropy(self, series: pd.Series) -> pd.Series:
        probabilities = series.value_counts(normalize=True)
        entropy = float(-(probabilities * np.log2(probabilities + 1e-12)).sum())
        return pd.Series(np.repeat(entropy, len(series)), index=series.index)

    def _activity_switch_rate(self, series: pd.Series) -> pd.Series:
        if len(series) <= 1:
            return pd.Series(np.zeros(len(series)), index=series.index)
        switches = (series != series.shift()).fillna(False).astype(np.int8)
        rate = float(switches.sum() / max(len(series) - 1, 1))
        return pd.Series(np.repeat(rate, len(series)), index=series.index)

    def _burstiness_score(self, series: pd.Series) -> pd.Series:
        mean_interval = float(series.mean())
        std_interval = float(series.std())
        denominator = std_interval + mean_interval
        burstiness = 0.0 if denominator == 0 else (std_interval - mean_interval) / denominator
        return pd.Series(np.repeat(burstiness, len(series)), index=series.index)

    def _drop_highly_correlated(self, frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
        numeric = frame.select_dtypes(include=["number"]).drop(columns=["row_id"], errors="ignore")
        if numeric.empty:
            return frame
        correlation = numeric.corr().abs()
        upper = correlation.where(np.triu(np.ones(correlation.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
        return frame.drop(columns=to_drop, errors="ignore")
