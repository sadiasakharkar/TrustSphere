"""Central configuration for the TrustSphere UEBA anomaly pipeline."""

from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

DEFAULT_DATASET_PATH = RAW_DATA_DIR / "logon.csv"
MODEL_VERSION = "ueba-iforest-v1.0.0"
CONTAMINATION_RATE = 0.02
RANDOM_STATE = 42
FEATURE_WINDOW_HOURS = 24
SHORT_WINDOW_HOURS = 1
DEVICE_WINDOW_DAYS = 7
TSFRESH_ENABLED = True
PCA_ENABLED = False
PCA_VARIANCE = 0.95

MIN_REQUIRED_COLUMNS = ["timestamp", "user", "host", "event_type", "status"]
