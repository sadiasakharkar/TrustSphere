from __future__ import annotations

import os

# Keep local math libs conservative to avoid OpenMP runtime crashes on some demo hosts.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

ML_IMPORT_ERROR = None
ML_RUNTIME_ENABLED = os.getenv("TRUSTSPHERE_ENABLE_ML_RUNTIME", "0").strip().lower() in {"1", "true", "yes"}
ML_AVAILABLE = False

if ML_RUNTIME_ENABLED:
    try:
        import sklearn  # noqa: F401
        ML_AVAILABLE = True
    except Exception as exc:  # pragma: no cover - environment-specific
        ML_IMPORT_ERROR = str(exc)
        ML_AVAILABLE = False
else:
    ML_IMPORT_ERROR = "ML runtime disabled for resilient execution. Set TRUSTSPHERE_ENABLE_ML_RUNTIME=1 to enable live sklearn-based inference."


def check_ml_runtime() -> dict[str, object]:
    return {
        "enabled": ML_RUNTIME_ENABLED,
        "available": ML_AVAILABLE,
        "error": ML_IMPORT_ERROR,
    }


def simulate_anomaly_score(event: dict[str, object]) -> float:
    event_id = str(event.get("event_id") or event.get("id") or event.get("timestamp") or "trustsphere-event")
    return round((abs(hash(event_id)) % 100) / 100.0, 4)
