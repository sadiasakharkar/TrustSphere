"""Enterprise-grade behavioral feature engineering for TrustSphere UEBA."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_selection import VarianceThreshold
from sklearn.inspection import permutation_importance

try:
    from .config import ARTIFACTS_DIR, RANDOM_STATE
except ImportError:
    from config import ARTIFACTS_DIR, RANDOM_STATE

try:
    from tsfresh import extract_features
    from tsfresh.feature_extraction import EfficientFCParameters
    from tsfresh.utilities.dataframe_functions import impute

    TSFRESH_AVAILABLE = True
except Exception:
    TSFRESH_AVAILABLE = False


LOGGER = logging.getLogger(__name__)

EVENT_SIGNAL_MAP = {
    "login_success": 1,
    "login": 1,
    "logon": 1,
    "login_failed": -1,
    "failed_login": -1,
    "file_access": 2,
    "privilege_change": 3,
    "logout": 0,
    "logoff": 0,
}


@dataclass(slots=True)
class FeatureEngineeringResult:
    """Container for transformed behavioral features and metadata."""

    features_df: pd.DataFrame
    metadata_df: pd.DataFrame
    feature_columns: list[str]


class BehavioralFeatureEngineer:
    """Generate UEBA behavioral intelligence features from normalized logs."""

    def __init__(
        self,
        window_hours: int = 24,
        rolling_windows: list[int] | None = None,
        enable_tsfresh: bool = True,
        top_n_features: int = 128,
        chunk_size: int = 250_000,
    ) -> None:
        self.window_hours = window_hours
        self.rolling_windows = rolling_windows or [1, 6, 24]
        self.enable_tsfresh = enable_tsfresh and TSFRESH_AVAILABLE
        self.top_n_features = top_n_features
        self.chunk_size = chunk_size
        self.selected_feature_columns_: list[str] = []
        self.feature_metadata_: list[dict[str, Any]] = []
        self.feature_importance_: pd.DataFrame | None = None

    def fit_transform(self, df: pd.DataFrame) -> FeatureEngineeringResult:
        """Fit the selection logic and return the final numeric feature matrix."""
        engineered, metadata = self._build_feature_frame(df)
        selected, importance = self._select_features(engineered)
        self.selected_feature_columns_ = selected.columns.tolist()
        self.feature_importance_ = importance
        self._build_feature_metadata(selected.columns.tolist())
        self._save_artifacts()
        LOGGER.info(
            "Users processed: %s | Selected features: %s",
            metadata["user"].nunique(),
            len(self.selected_feature_columns_),
        )
        return FeatureEngineeringResult(
            features_df=selected,
            metadata_df=metadata,
            feature_columns=self.selected_feature_columns_,
        )

    def transform(self, df: pd.DataFrame) -> FeatureEngineeringResult:
        """Transform logs using the previously learned feature column ordering."""
        engineered, metadata = self._build_feature_frame(df)
        if self.selected_feature_columns_:
            for column in self.selected_feature_columns_:
                if column not in engineered.columns:
                    engineered[column] = 0.0
            engineered = engineered[self.selected_feature_columns_]
            feature_columns = self.selected_feature_columns_
        else:
            feature_columns = engineered.columns.tolist()
        engineered = self._sanitize_numeric_frame(engineered)
        return FeatureEngineeringResult(
            features_df=engineered,
            metadata_df=metadata,
            feature_columns=feature_columns,
        )

    def _build_feature_frame(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        frame = self._prepare_input(df)
        rolling_features = self._create_rolling_features(frame)
        tsfresh_features = self._extract_tsfresh_features(frame) if self.enable_tsfresh else pd.DataFrame(index=rolling_features.index)
        merged = pd.concat([rolling_features, tsfresh_features], axis=1)
        merged = merged.loc[:, ~merged.columns.duplicated()].copy()
        merged = self._drop_highly_correlated(merged, threshold=0.9)
        merged = self._sanitize_numeric_frame(merged)
        metadata = frame[["timestamp", "user", "host", "event_type", "status"]].copy()
        LOGGER.info(
            "Rolling features created: %s | tsfresh features extracted: %s",
            len(rolling_features.columns),
            len(tsfresh_features.columns),
        )
        return merged, metadata

    def _prepare_input(self, df: pd.DataFrame) -> pd.DataFrame:
        frame = df.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]

        required = {"timestamp", "user", "host", "event_type", "status"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "user", "host", "event_type", "status"]).copy()
        frame["user"] = frame["user"].astype(str).str.strip().str.lower()
        frame["host"] = frame["host"].astype(str).str.strip().str.lower()
        frame["event_type"] = frame["event_type"].astype(str).str.strip().str.lower()
        frame["status"] = frame["status"].astype(str).str.strip().str.lower()
        if "ip" in frame.columns and "ip_address" not in frame.columns:
            frame["ip_address"] = frame["ip"]
        if "ip_address" in frame.columns:
            frame["ip_address"] = frame["ip_address"].astype(str).str.strip().str.lower()

        frame = frame.sort_values(["user", "timestamp"]).reset_index(drop=True)
        frame["row_id"] = np.arange(len(frame), dtype=np.int64)
        frame["login_hour"] = frame["timestamp"].dt.hour.astype(np.int16)
        frame["day_of_week"] = frame["timestamp"].dt.dayofweek.astype(np.int8)
        frame["weekend_flag"] = (frame["day_of_week"] >= 5).astype(np.int8)
        frame["night_flag"] = ((frame["login_hour"] < 6) | (frame["login_hour"] >= 21)).astype(np.int8)
        frame["event_signal"] = frame["event_type"].map(EVENT_SIGNAL_MAP).fillna(0).astype(np.float32)
        frame["is_login"] = frame["event_type"].str.contains("logon|login", regex=True).astype(np.int8)
        frame["is_failed_login"] = (
            frame["status"].isin(["fail", "failed", "denied", "error"])
            | frame["event_type"].str.contains("failed", regex=False)
        ).astype(np.int8)
        frame["previous_timestamp"] = frame.groupby("user", sort=False)["timestamp"].shift()
        frame["activity_interval_minutes"] = (
            (frame["timestamp"] - frame["previous_timestamp"]).dt.total_seconds().div(60.0).fillna(0.0)
        )
        frame["previous_host"] = frame.groupby("user", sort=False)["host"].shift()
        if "ip_address" in frame.columns:
            frame["previous_ip_address"] = frame.groupby("user", sort=False)["ip_address"].shift()
        return frame

    def _create_rolling_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        outputs: list[pd.DataFrame] = []
        for _, user_frame in frame.groupby("user", sort=False):
            outputs.append(self._process_user_chunk(user_frame))
        feature_frame = pd.concat(outputs).sort_index()
        numeric_frame = feature_frame.select_dtypes(include=["number", "bool"]).copy()
        return numeric_frame

    def _process_user_chunk(self, user_frame: pd.DataFrame) -> pd.DataFrame:
        user_frame = user_frame.copy()
        indexed = user_frame.set_index("timestamp")
        feature_frame = pd.DataFrame(index=user_frame.index)

        feature_frame["event_signal"] = user_frame["event_signal"].to_numpy(dtype=np.float32)
        feature_frame["login_hour"] = user_frame["login_hour"].to_numpy(dtype=np.float32)
        feature_frame["day_of_week"] = user_frame["day_of_week"].to_numpy(dtype=np.float32)
        feature_frame["weekend_flag"] = user_frame["weekend_flag"].to_numpy(dtype=np.float32)
        feature_frame["night_activity_ratio"] = indexed["night_flag"].rolling("24h", min_periods=1).mean().to_numpy(dtype=np.float32)
        feature_frame["mean_activity_interval"] = user_frame["activity_interval_minutes"].to_numpy(dtype=np.float32)
        feature_frame["std_session_duration"] = (
            indexed["activity_interval_minutes"].rolling("24h", min_periods=2).std().fillna(0.0).to_numpy(dtype=np.float32)
        )
        feature_frame["event_entropy"] = self._rolling_entropy(indexed["event_type"], window="24h")
        feature_frame["activity_switch_rate"] = self._activity_switch_rate(user_frame)
        feature_frame["burstiness_score"] = self._rolling_burstiness(indexed["activity_interval_minutes"], window="24h")
        feature_frame["new_device_flag"] = self._new_device_flags(user_frame)
        feature_frame["device_change_flag"] = (
            (user_frame["previous_host"].notna() & (user_frame["host"] != user_frame["previous_host"])).astype(np.float32)
        )
        feature_frame["device_change_rate"] = feature_frame["device_change_flag"].expanding().mean().astype(np.float32)

        if "ip_address" in user_frame.columns:
            ip_switch_flag = (
                user_frame["previous_ip_address"].notna()
                & (user_frame["ip_address"] != user_frame["previous_ip_address"])
            ).astype(np.float32)
            feature_frame["ip_switch_rate"] = ip_switch_flag.expanding().mean().astype(np.float32)
        else:
            feature_frame["ip_switch_rate"] = 0.0

        for hours in self.rolling_windows:
            window = f"{hours}h"
            feature_frame[f"event_count_{window}"] = (
                indexed["event_signal"].rolling(window, min_periods=1).count().to_numpy(dtype=np.float32)
            )
            feature_frame[f"login_rate_{window}"] = (
                indexed["is_login"].rolling(window, min_periods=1).mean().to_numpy(dtype=np.float32)
            )
            feature_frame[f"failed_login_ratio_{window}"] = (
                indexed["is_failed_login"].rolling(window, min_periods=1).mean().to_numpy(dtype=np.float32)
            )
            feature_frame[f"rolling_mean_activity_{window}"] = (
                indexed["event_signal"].rolling(window, min_periods=1).mean().to_numpy(dtype=np.float32)
            )
            feature_frame[f"rolling_std_activity_{window}"] = (
                indexed["event_signal"].rolling(window, min_periods=1).std().fillna(0.0).to_numpy(dtype=np.float32)
            )
            feature_frame[f"rolling_max_activity_{window}"] = (
                indexed["event_signal"].rolling(window, min_periods=1).max().to_numpy(dtype=np.float32)
            )
            feature_frame[f"rolling_min_activity_{window}"] = (
                indexed["event_signal"].rolling(window, min_periods=1).min().to_numpy(dtype=np.float32)
            )
            feature_frame[f"activity_delta_{window}"] = (
                feature_frame[f"rolling_mean_activity_{window}"].diff().fillna(0.0).astype(np.float32)
            )

        if "ip_address" in user_frame.columns:
            feature_frame["unique_ips_24h"] = self._rolling_unique(indexed["ip_address"], window="24h")
        feature_frame["unique_hosts_24h"] = self._rolling_unique(indexed["host"], window="24h")
        return feature_frame

    def _extract_tsfresh_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        tsfresh_input = frame[["user", "timestamp", "event_signal"]].rename(columns={"user": "id", "event_signal": "value"})
        ts_features = extract_features(
            tsfresh_input,
            column_id="id",
            column_sort="timestamp",
            default_fc_parameters=EfficientFCParameters(),
            disable_progressbar=True,
            n_jobs=0,
        )
        ts_features = impute(ts_features)
        ts_features.index.name = "user"
        user_level = frame[["user"]].copy()
        user_level = user_level.merge(ts_features.reset_index(), on="user", how="left").drop(columns=["user"])
        user_level.index = frame.index
        return user_level.astype(np.float32)

    def _select_features(self, features_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        variance_selector = VarianceThreshold(0.01)
        selected_array = variance_selector.fit_transform(features_df)
        selected_columns = features_df.columns[variance_selector.get_support()].tolist()
        selected_df = pd.DataFrame(selected_array, columns=selected_columns, index=features_df.index)

        temp_model = IsolationForest(
            n_estimators=200,
            contamination=0.02,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        temp_model.fit(selected_df)
        pseudo_labels = (temp_model.decision_function(selected_df) < 0).astype(int)
        importance = permutation_importance(
            temp_model,
            selected_df,
            pseudo_labels,
            scoring=_unsupervised_permutation_scorer,
            n_repeats=5,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
        importance_df = pd.DataFrame(
            {
                "feature_name": selected_columns,
                "importance_score": importance.importances_mean,
            }
        ).sort_values("importance_score", ascending=False)

        top_features = importance_df.head(min(self.top_n_features, len(importance_df)))["feature_name"].tolist()
        selected_df = selected_df[top_features].copy()
        return selected_df, importance_df

    def _build_feature_metadata(self, feature_columns: list[str]) -> None:
        metadata: list[dict[str, Any]] = []
        for column in feature_columns:
            creation_method = "tsfresh" if "__" in column else "rolling"
            window_size = None
            for hours in self.rolling_windows:
                suffix = f"{hours}h"
                if suffix in column:
                    window_size = suffix
                    break
            metadata.append(
                {
                    "feature_name": column,
                    "creation_method": creation_method,
                    "window_size": window_size,
                }
            )
        self.feature_metadata_ = metadata

    def _save_artifacts(self) -> None:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        if self.feature_importance_ is not None:
            self.feature_importance_.to_csv(ARTIFACTS_DIR / "feature_importance.csv", index=False)
        with (ARTIFACTS_DIR / "feature_columns.json").open("w", encoding="utf-8") as handle:
            json.dump(self.feature_metadata_, handle, indent=2)

    def _sanitize_numeric_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric = frame.select_dtypes(include=["number", "bool"]).copy()
        numeric = numeric.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        numeric = numeric.astype(np.float32)
        return numeric.reindex(sorted(numeric.columns), axis=1)

    def _drop_highly_correlated(self, frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
        if frame.empty or frame.shape[1] < 2:
            return frame
        correlation = frame.corr(method="spearman").abs()
        upper_triangle = correlation.where(np.triu(np.ones(correlation.shape), k=1).astype(bool))
        to_drop = [column for column in upper_triangle.columns if (upper_triangle[column] > threshold).any()]
        if to_drop:
            LOGGER.info("Dropping %s highly correlated features", len(to_drop))
        return frame.drop(columns=to_drop, errors="ignore")

    def _rolling_entropy(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            probabilities = window_values.value_counts(normalize=True)
            entropy = float(-(probabilities * np.log2(probabilities + 1e-12)).sum()) if not probabilities.empty else 0.0
            values.append(entropy)
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _rolling_burstiness(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            mean_value = float(window_values.mean()) if not window_values.empty else 0.0
            std_value = float(window_values.std()) if not window_values.empty else 0.0
            denominator = mean_value + std_value
            burstiness = 0.0 if denominator == 0 else (std_value - mean_value) / denominator
            values.append(burstiness)
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _rolling_unique(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            values.append(float(window_values.nunique()))
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _new_device_flags(self, user_frame: pd.DataFrame) -> pd.Series:
        seen_hosts: set[str] = set()
        flags: list[float] = []
        for host in user_frame["host"].astype(str):
            flags.append(0.0 if host in seen_hosts else 1.0)
            seen_hosts.add(host)
        return pd.Series(flags, index=user_frame.index, dtype=np.float32)

    def _activity_switch_rate(self, user_frame: pd.DataFrame) -> pd.Series:
        switches = (user_frame["event_type"] != user_frame["event_type"].shift()).fillna(False).astype(np.float32)
        rate = switches.expanding().mean().astype(np.float32)
        return pd.Series(rate.to_numpy(), index=user_frame.index)


def _unsupervised_permutation_scorer(estimator: Any, x_values: Any, y_values: Any | None = None) -> float:
    scores = -np.asarray(estimator.score_samples(x_values), dtype=float)
    return float(np.std(scores))


if __name__ == "__main__":
    try:
        default_path = ARTIFACTS_DIR.parent / "data" / "raw" / "logon.csv"
        raw_df = pd.read_csv(default_path)
        raw_df.columns = [str(column).strip().lower() for column in raw_df.columns]
        if "date" in raw_df.columns and "timestamp" not in raw_df.columns:
            raw_df = raw_df.rename(columns={"date": "timestamp"})
        if "pc" in raw_df.columns and "host" not in raw_df.columns:
            raw_df = raw_df.rename(columns={"pc": "host"})
        if "activity" in raw_df.columns and "event_type" not in raw_df.columns:
            raw_df = raw_df.rename(columns={"activity": "event_type"})
        if "status" not in raw_df.columns:
            raw_df["status"] = np.where(raw_df["event_type"].astype(str).str.contains("fail", case=False), "failed", "success")

        engineer = BehavioralFeatureEngineer()
        result = engineer.fit_transform(raw_df)
        print(f"Feature Count: {len(result.feature_columns)}")
        print(f"Rows Processed: {len(result.features_df)}")
        if engineer.feature_importance_ is not None:
            print("Top Important Features:")
            print(engineer.feature_importance_.head(10).to_string(index=False))
    except Exception as exc:
        LOGGER.exception("Feature engineering test runner failed: %s", exc)
