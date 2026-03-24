"""Prometheus metrics for the TrustSphere Security AI API."""

from __future__ import annotations

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

    def generate_latest():
        return b"# Prometheus client not installed\n"


REQUEST_COUNTER = Counter(
    "trustsphere_requests_total",
    "Total API requests processed by endpoint and status.",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "trustsphere_request_latency_seconds",
    "Latency for API requests.",
    ["endpoint"],
)
FALSE_POSITIVE_GAUGE = Gauge(
    "trustsphere_false_positive_rate",
    "False positive rate reported by detection models.",
    ["detector"],
)
MODEL_DRIFT_GAUGE = Gauge(
    "trustsphere_model_drift_score",
    "Model drift score reported by offline evaluators.",
    ["detector"],
)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
