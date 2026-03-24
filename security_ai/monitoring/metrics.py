"""Prometheus metrics and observability helpers for TrustSphere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except Exception:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    PROMETHEUS_AVAILABLE = False

    class _Metric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

        def set(self, *args, **kwargs):
            return None

    Counter = Gauge = Histogram = lambda *args, **kwargs: _Metric()  # type: ignore

    def generate_latest() -> bytes:
        return b"# Prometheus client not installed\n"


REQUEST_COUNTER = Counter("trustsphere_requests_total", "API requests processed.", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("trustsphere_request_latency_seconds", "API request latency.", ["endpoint"])
INFERENCE_LATENCY = Histogram("trustsphere_inference_latency_seconds", "Model inference latency.", ["detector"])
ANOMALY_RATE = Gauge("trustsphere_anomaly_rate", "Observed anomaly rate.", ["detector"])
FALSE_POSITIVE_ESTIMATE = Gauge("trustsphere_false_positive_estimate", "Estimated false positive rate.", ["detector"])
MODEL_DRIFT_INDICATOR = Gauge("trustsphere_model_drift_indicator", "Estimated model drift indicator.", ["detector"])


@dataclass(slots=True)
class MetricsSnapshot:
    detector: str
    false_positive_estimate: float = 0.0
    model_drift_indicator: float = 0.0
    anomaly_rate: float = 0.0


def record_model_snapshot(snapshot: MetricsSnapshot) -> None:
    FALSE_POSITIVE_ESTIMATE.labels(snapshot.detector).set(snapshot.false_positive_estimate)
    MODEL_DRIFT_INDICATOR.labels(snapshot.detector).set(snapshot.model_drift_indicator)
    ANOMALY_RATE.labels(snapshot.detector).set(snapshot.anomaly_rate)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
