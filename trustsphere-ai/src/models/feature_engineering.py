"""Core behavioral feature engineering for the TrustSphere UEBA pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold, mutual_info_classif

try:
    from tsfresh import extract_features
    from tsfresh.feature_extraction import EfficientFCParameters
    from tsfresh.utilities.dataframe_functions import impute as tsfresh_impute

    TSFRESH_AVAILABLE = True
except Exception:
    TSFRESH_AVAILABLE = False

try:
    from .config import (
        ARTIFACTS_DIR,
        CACHE_DIR,
        FEATURE_MAX_COUNT,
        RANDOM_STATE,
        ROLLING_WINDOWS_MINUTES,
        TSFRESH_N_JOBS,
    )
except ImportError:
    from config import (
        ARTIFACTS_DIR,
        CACHE_DIR,
        FEATURE_MAX_COUNT,
        RANDOM_STATE,
        ROLLING_WINDOWS_MINUTES,
        TSFRESH_N_JOBS,
    )


LOGGER = logging.getLogger(__name__)
EVENT_SIGNAL_MAP = {
    "login_success": 1.0,
    "login": 1.0,
    "logon": 1.0,
    "login_failed": -1.0,
    "failed_login": -1.0,
    "file_access": 2.0,
    "privilege_change": 3.0,
    "privilege_escalation": 3.5,
    "admin_action": 3.0,
    "logout": 0.0,
    "logoff": 0.0,
    "command_execution": 2.5,
    "data_exfiltration": 4.0,
}


@dataclass(slots=True)
class FeatureEngineeringArtifacts:
    timeseries_features: pd.DataFrame
    behavioral_features: pd.DataFrame
    selected_features: pd.DataFrame
    metadata_df: pd.DataFrame
    selected_columns: list[str]


class BehavioralFeatureEngineer:
    """Build UEBA-ready features from normalized security logs."""

    def __init__(
        self,
        entity_column: str | None = None,
        enable_tsfresh: bool = True,
        rolling_windows: list[int] | None = None,
        feature_cache_dir: str | Path = CACHE_DIR,
        max_features: int = FEATURE_MAX_COUNT,
    ) -> None:
        self.entity_column = entity_column
        self.enable_tsfresh = enable_tsfresh and TSFRESH_AVAILABLE
        self.rolling_windows = rolling_windows or ROLLING_WINDOWS_MINUTES
        self.feature_cache_dir = Path(feature_cache_dir)
        self.max_features = max_features
        self.selected_columns_: list[str] = []
        self.selection_metadata_: dict[str, Any] = {}

    def fit_transform(self, dataframe: pd.DataFrame) -> FeatureEngineeringArtifacts:
        frame = self._prepare_frame(dataframe)
        metadata = frame.groupby("entity_id", sort=False)["timestamp"].max().reset_index()
        timeseries = self.extract_timeseries_features(frame)
        behavioral = self.extract_behavioral_features(frame)
        merged = self._merge_feature_sets(metadata, timeseries, behavioral)
        selected = self.select_features(merged, frame)
        self._save_feature_schema(selected.columns.tolist())
        return FeatureEngineeringArtifacts(
            timeseries_features=timeseries,
            behavioral_features=behavioral,
            selected_features=selected,
            metadata_df=metadata,
            selected_columns=selected.columns.tolist(),
        )

    def transform(self, dataframe: pd.DataFrame) -> FeatureEngineeringArtifacts:
        frame = self._prepare_frame(dataframe)
        metadata = frame.groupby("entity_id", sort=False)["timestamp"].max().reset_index()
        timeseries = self.extract_timeseries_features(frame)
        behavioral = self.extract_behavioral_features(frame)
        merged = self._merge_feature_sets(metadata, timeseries, behavioral)
        if self.selected_columns_:
            for column in self.selected_columns_:
                if column not in merged.columns:
                    merged[column] = 0.0
            merged = merged[self.selected_columns_]
        merged = self._sanitize_numeric(merged)
        return FeatureEngineeringArtifacts(
            timeseries_features=timeseries,
            behavioral_features=behavioral,
            selected_features=merged,
            metadata_df=metadata,
            selected_columns=merged.columns.tolist(),
        )

    def extract_timeseries_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        cache_key = self._cache_key(frame[["entity_id", "timestamp", "event_signal", "bytes_sent", "bytes_received"]])
        cache_path = self.feature_cache_dir / f"tsfresh_{cache_key}.joblib"
        if cache_path.exists():
            tsfresh_features = joblib.load(cache_path)
            LOGGER.info("Loaded cached time-series features from %s", cache_path)
        else:
            if self.enable_tsfresh:
                tsfresh_features = self._run_tsfresh(frame)
            else:
                tsfresh_features = self._manual_timeseries_features(frame)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(tsfresh_features, cache_path)

        output_path = ARTIFACTS_DIR / "features_timeseries.parquet"
        self._save_dataframe(tsfresh_features, output_path)
        return tsfresh_features

    def extract_behavioral_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        outputs: list[pd.DataFrame] = []
        for _, entity_frame in frame.groupby("entity_id", sort=False):
            outputs.append(self._build_behavioral_windows(entity_frame))
        behavioral = pd.concat(outputs, axis=0).sort_index()
        behavioral = behavioral.groupby(level=0).last()
        behavioral = self._sanitize_numeric(behavioral)
        self._save_dataframe(behavioral, ARTIFACTS_DIR / "features_behavioral.parquet")
        return behavioral

    def select_features(self, features_df: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
        numeric = self._sanitize_numeric(features_df)
        variance_selector = VarianceThreshold(0.0)
        reduced_array = variance_selector.fit_transform(numeric)
        reduced_columns = numeric.columns[variance_selector.get_support()].tolist()
        reduced = pd.DataFrame(reduced_array, index=numeric.index, columns=reduced_columns)

        correlation = reduced.corr().abs()
        upper = correlation.where(np.triu(np.ones(correlation.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if (upper[column] > 0.9).any()]
        reduced = reduced.drop(columns=to_drop, errors="ignore")

        pseudo_labels = self._build_pseudo_labels(frame)
        aligned_labels = pseudo_labels.reindex(reduced.index).fillna(0).astype(int)
        mi_scores = mutual_info_classif(reduced, aligned_labels, discrete_features=False, random_state=RANDOM_STATE)
        mi_ranking = pd.Series(mi_scores, index=reduced.columns).sort_values(ascending=False)
        top_candidates = mi_ranking.head(min(max(self.max_features * 2, 20), len(mi_ranking))).index.tolist()
        candidate_df = reduced[top_candidates].copy()

        estimator = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)
        target_feature_count = min(self.max_features, max(5, len(candidate_df.columns)))
        if len(candidate_df.columns) > target_feature_count:
            selector = RFE(estimator=estimator, n_features_to_select=target_feature_count, step=0.1)
            selector.fit(candidate_df, aligned_labels)
            final_columns = candidate_df.columns[selector.get_support()].tolist()
        else:
            final_columns = candidate_df.columns.tolist()

        selected = candidate_df[final_columns].copy()
        self.selected_columns_ = final_columns
        self.selection_metadata_ = {
            "variance_retained": len(reduced_columns),
            "correlation_dropped": len(to_drop),
            "mutual_information_ranked": len(top_candidates),
            "selected_count": len(final_columns),
        }
        joblib.dump(final_columns, ARTIFACTS_DIR / "selected_features.pkl")
        LOGGER.info("Selected %s features after multi-stage filtering", len(final_columns))
        return selected

    def _prepare_frame(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        frame = dataframe.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if "timestamp" not in frame.columns:
            raise ValueError("Input dataframe must contain a timestamp column.")
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).copy()

        entity_column = self.entity_column or self._infer_entity_column(frame)
        frame["entity_id"] = frame[entity_column].astype(str).str.strip().str.lower()
        frame["event_type"] = self._series_or_default(frame, "event_type", "unknown_event").astype(str).str.strip().str.lower()
        frame["status"] = self._series_or_default(frame, "status", "unknown").astype(str).str.strip().str.lower()
        frame["ip"] = self._series_or_default(frame, "ip", frame.get("ip_address"), "unknown").astype(str).str.strip().str.lower()
        frame["location"] = self._series_or_default(frame, "location", "unknown").astype(str).str.strip().str.lower()
        frame["command"] = self._series_or_default(frame, "command", frame.get("process_name"), "unknown").astype(str).str.strip().str.lower()
        frame["bytes_sent"] = pd.to_numeric(self._series_or_default(frame, "bytes_sent", 0.0), errors="coerce").fillna(0.0)
        frame["bytes_received"] = pd.to_numeric(self._series_or_default(frame, "bytes_received", 0.0), errors="coerce").fillna(0.0)
        frame["failed_attempts"] = pd.to_numeric(self._series_or_default(frame, "failed_attempts", 0), errors="coerce").fillna(0)
        frame["event_signal"] = frame["event_type"].map(EVENT_SIGNAL_MAP).fillna(0.5).astype(np.float32)
        frame["is_login"] = frame["event_type"].str.contains("login|logon", regex=True).astype(np.int8)
        frame["is_failed_login"] = (
            frame["status"].isin(["fail", "failed", "error", "denied"]) |
            frame["event_type"].str.contains("failed", regex=False)
        ).astype(np.int8)
        frame["is_privilege_escalation"] = frame["event_type"].str.contains("privilege|admin_action", regex=True).astype(np.int8)
        frame = frame.sort_values(["entity_id", "timestamp"]).reset_index(drop=True)
        return frame

    def _infer_entity_column(self, frame: pd.DataFrame) -> str:
        for candidate in ["user_id", "host_id", "user", "host"]:
            if candidate in frame.columns:
                return candidate
        raise ValueError("Unable to infer entity column from input dataframe.")

    def _series_or_default(
        self,
        frame: pd.DataFrame,
        primary: str,
        secondary: pd.Series | str | float | int | None = None,
        default: str | float | int | None = None,
    ) -> pd.Series:
        if primary in frame.columns:
            return frame[primary]
        if isinstance(secondary, pd.Series):
            return secondary
        if secondary is not None and not isinstance(secondary, (str, float, int)):
            return pd.Series(secondary, index=frame.index)
        fallback_value = secondary if secondary is not None and default is None else default
        return pd.Series([fallback_value] * len(frame), index=frame.index)

    def _run_tsfresh(self, frame: pd.DataFrame) -> pd.DataFrame:
        ts_frame = frame[["entity_id", "timestamp", "event_signal", "bytes_sent", "bytes_received", "failed_attempts"]].copy()
        long_frame = pd.concat(
            [
                ts_frame[["entity_id", "timestamp", "event_signal"]].rename(columns={"entity_id": "id", "event_signal": "value"}).assign(kind="event_signal"),
                ts_frame[["entity_id", "timestamp", "bytes_sent"]].rename(columns={"entity_id": "id", "bytes_sent": "value"}).assign(kind="bytes_sent"),
                ts_frame[["entity_id", "timestamp", "bytes_received"]].rename(columns={"entity_id": "id", "bytes_received": "value"}).assign(kind="bytes_received"),
                ts_frame[["entity_id", "timestamp", "failed_attempts"]].rename(columns={"entity_id": "id", "failed_attempts": "value"}).assign(kind="failed_attempts"),
            ],
            ignore_index=True,
        )
        extracted = extract_features(
            long_frame,
            column_id="id",
            column_sort="timestamp",
            column_kind="kind",
            column_value="value",
            default_fc_parameters=EfficientFCParameters(),
            impute_function=tsfresh_impute,
            disable_progressbar=True,
            n_jobs=TSFRESH_N_JOBS,
        )
        extracted.index.name = "entity_id"
        return extracted.astype(np.float32)

    def _manual_timeseries_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        grouped = frame.groupby("entity_id", sort=False)
        rows = []
        for entity_id, entity_frame in grouped:
            signal = entity_frame["event_signal"].astype(float)
            delta = entity_frame["timestamp"].diff().dt.total_seconds().fillna(0.0)
            rows.append(
                {
                    "entity_id": entity_id,
                    "ts_event_frequency": float(len(entity_frame)),
                    "ts_entropy": self._entropy(entity_frame["event_type"]),
                    "ts_variance": float(signal.var(ddof=0) if len(signal) > 1 else 0.0),
                    "ts_periodicity": float(delta.std(ddof=0) if len(delta) > 1 else 0.0),
                    "ts_spike_ratio": float((signal.abs() > signal.abs().quantile(0.9)).mean()) if len(signal) > 0 else 0.0,
                    "ts_behavioral_drift": float(signal.diff().abs().mean() if len(signal) > 1 else 0.0),
                }
            )
        return pd.DataFrame(rows).set_index("entity_id")

    def _build_behavioral_windows(self, entity_frame: pd.DataFrame) -> pd.DataFrame:
        indexed = entity_frame.set_index("timestamp")
        feature_frame = pd.DataFrame(index=entity_frame.index)
        for window_minutes in self.rolling_windows:
            window = f"{window_minutes}min"
            suffix = self._window_suffix(window_minutes)
            feature_frame[f"login_count_{suffix}"] = indexed["is_login"].rolling(window, min_periods=1).sum().to_numpy(dtype=np.float32)
            feature_frame[f"failed_login_ratio_{suffix}"] = indexed["is_failed_login"].rolling(window, min_periods=1).mean().to_numpy(dtype=np.float32)
            feature_frame[f"unique_ip_count_{suffix}"] = self._rolling_nunique(indexed["ip"], window)
            feature_frame[f"geo_switch_rate_{suffix}"] = self._rolling_switch_rate(indexed["location"], window)
            feature_frame[f"privilege_escalation_count_{suffix}"] = indexed["is_privilege_escalation"].rolling(window, min_periods=1).sum().to_numpy(dtype=np.float32)
            feature_frame[f"command_entropy_{suffix}"] = self._rolling_entropy(indexed["command"], window)
        feature_frame["entity_id"] = entity_frame["entity_id"].to_numpy()
        return feature_frame.groupby("entity_id").last()

    def _merge_feature_sets(
        self,
        metadata: pd.DataFrame,
        timeseries_df: pd.DataFrame,
        behavioral_df: pd.DataFrame,
    ) -> pd.DataFrame:
        entity_index = metadata[["entity_id"]].drop_duplicates().set_index("entity_id")
        merged = entity_index.join(timeseries_df, how="left").join(behavioral_df, how="left")
        return self._sanitize_numeric(merged)

    def _build_pseudo_labels(self, frame: pd.DataFrame) -> pd.Series:
        if "label" in frame.columns:
            labels = frame["label"].astype(str).str.lower().isin(["attack", "suspicious", "anomaly"]).astype(int)
            return frame.assign(label_value=labels).groupby("entity_id")["label_value"].max()
        heuristic = (
            (frame["is_failed_login"] == 1)
            | (frame["is_privilege_escalation"] == 1)
            | (frame["bytes_sent"] > frame["bytes_sent"].quantile(0.95))
        ).astype(int)
        return frame.assign(label_value=heuristic).groupby("entity_id")["label_value"].max()

    def _sanitize_numeric(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric = frame.select_dtypes(include=["number", "bool"]).copy()
        numeric = numeric.replace([np.inf, -np.inf], np.nan)
        numeric = numeric.fillna(numeric.median(numeric_only=True))
        numeric = numeric.fillna(0.0).astype(np.float32)
        numeric = numeric.reindex(sorted(numeric.columns), axis=1)
        return numeric

    def _cache_key(self, frame: pd.DataFrame) -> str:
        fingerprint = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
        return hashlib.sha256(fingerprint).hexdigest()[:16]

    def _save_dataframe(self, dataframe: pd.DataFrame, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            dataframe.to_parquet(output_path)
        except Exception as exc:
            if _strict_production_mode():
                raise RuntimeError(f"Parquet export failed for {output_path} in production mode.") from exc
            fallback_path = output_path.with_suffix(".csv")
            dataframe.to_csv(fallback_path)
            LOGGER.warning("Parquet export failed for %s (%s). Wrote CSV fallback to %s", output_path, exc, fallback_path)

    def _save_feature_schema(self, columns: list[str]) -> None:
        schema = [
            {
                "feature_name": column,
                "source": "timeseries" if column.startswith("ts_") or "__" in column else "behavioral",
            }
            for column in columns
        ]
        (ARTIFACTS_DIR / "feature_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")

    def _window_suffix(self, minutes: int) -> str:
        if minutes < 60:
            return f"{minutes}m"
        if minutes < 1440:
            return f"{minutes // 60}h"
        return f"{minutes // 1440}d"

    def _rolling_nunique(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            values.append(float(window_values.nunique()))
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _rolling_switch_rate(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            switches = (window_values != window_values.shift()).fillna(False)
            values.append(float(switches.mean()))
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _rolling_entropy(self, series: pd.Series, window: str) -> pd.Series:
        values = []
        for current_timestamp in series.index:
            start_timestamp = current_timestamp - pd.Timedelta(window)
            window_values = series.loc[(series.index > start_timestamp) & (series.index <= current_timestamp)]
            values.append(self._entropy(window_values))
        return pd.Series(values, index=series.index, dtype=np.float32).reset_index(drop=True)

    def _entropy(self, series: pd.Series) -> float:
        probabilities = pd.Series(series).value_counts(normalize=True)
        if probabilities.empty:
            return 0.0
        return float(-(probabilities * np.log2(probabilities + 1e-12)).sum())


def _strict_production_mode() -> bool:
    return os.getenv("TRUSTSPHERE_ENV", "development").strip().lower() in {"prod", "production"}
