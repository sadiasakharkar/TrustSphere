"""Central configuration for the TrustSphere UEBA detection pipeline."""

from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ANOMALY_ARTIFACTS_DIR = ARTIFACTS_DIR / "anomaly_model"
SCALER_ARTIFACTS_DIR = ARTIFACTS_DIR / "scaler"
CACHE_DIR = ARTIFACTS_DIR / "cache"
MLRUNS_DIR = BASE_DIR / "mlruns"

DEFAULT_DATASET_PATH = RAW_DATA_DIR / "logon.csv"
FALLBACK_DATASET_PATH = RAW_DATA_DIR / "enterprise_logs.json"
MODEL_VERSION = "ueba-core-v2.0.0"
RANDOM_STATE = 42
CONTAMINATION_RATE = 0.02
FEATURE_MAX_COUNT = 100
TSFRESH_N_JOBS = 0
ROLLING_WINDOWS_MINUTES = [5, 60, 1440]
TIME_AWARE_SPLITS = (0.7, 0.15, 0.15)
AUTOENCODER_EPOCHS = 12
AUTOENCODER_BATCH_SIZE = 256
AUTOENCODER_LEARNING_RATE = 1e-3
AUTOENCODER_THRESHOLD_QUANTILE = 0.98
TOP_K_FRACTION = 0.05

ENTITY_COLUMN_CANDIDATES = ["user_id", "host_id", "user", "host"]
TIMESTAMP_COLUMN = "timestamp"
DEFAULT_ENTITY_COLUMN = "entity_id"

MIN_REQUIRED_COLUMNS = ["timestamp", "event_type"]
