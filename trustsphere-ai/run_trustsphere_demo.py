"""Run the full offline TrustSphere demo pipeline end to end.

Execution order:
1. Generate enterprise telemetry with the behavioral simulator.
2. Ensure the UEBA model artifacts exist, training them if necessary.
3. Analyze the incident through the unified TrustSphere pipeline.
4. Export demo-ready artifacts for reports, visuals, and metrics.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any

import networkx as nx
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.contracts import NormalizedLog

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

LOGGER = logging.getLogger("trustsphere_demo")
OUTPUTS_DIR = BASE_DIR / "outputs"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
PLACEHOLDER_PNG = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9s3Fo6kAAAAASUVORK5CYII="
)


def run_demo(n_users: int = 120, days: int = 2) -> dict[str, Any]:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    configure_logging()
    save_logs, run_training, TrustSpherePipeline = _load_demo_dependencies()

    timings: dict[str, float] = {}

    simulator_start = time.perf_counter()
    simulator_output = save_logs(n_users=n_users, days=days, output_path=RAW_DATA_DIR / "enterprise_logs.json")
    raw_logs = json.loads(simulator_output.read_text(encoding="utf-8"))
    normalized_logs = [adapt_simulator_event(event) for event in raw_logs]
    timings["simulation_seconds"] = round(time.perf_counter() - simulator_start, 4)

    training_metrics: dict[str, Any] = {}
    training_start = time.perf_counter()
    if needs_training():
        LOGGER.info("UEBA model artifacts missing. Training from simulator output.")
        training_artifacts = run_training(simulator_output)
        training_metrics = training_artifacts.metrics
    else:
        LOGGER.info("Using existing trained UEBA artifacts from %s", SAVED_MODELS_DIR)
    timings["training_seconds"] = round(time.perf_counter() - training_start, 4)

    inference_start = time.perf_counter()
    pipeline = TrustSpherePipeline(BASE_DIR)
    incident_report = pipeline.analyze_incident(normalized_logs)
    timings["analysis_seconds"] = round(time.perf_counter() - inference_start, 4)

    report_path = OUTPUTS_DIR / "incident_report.json"
    report_path.write_text(json.dumps(incident_report.model_dump(mode="json"), indent=2), encoding="utf-8")

    attack_graph_png = OUTPUTS_DIR / "attack_graph.png"
    graph_rendered = export_attack_graph_png(incident_report.attack_graph.model_dump(mode="json"), attack_graph_png)

    metrics_path = OUTPUTS_DIR / "metrics.json"
    metrics_payload = build_metrics_payload(
        raw_logs=raw_logs,
        normalized_logs=normalized_logs,
        incident_report=incident_report.model_dump(mode="json"),
        timings=timings,
        training_metrics=training_metrics,
        graph_rendered=graph_rendered,
    )
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    LOGGER.info("TrustSphere demo completed. Artifacts written to %s", OUTPUTS_DIR)
    return {
        "incident_report": str(report_path),
        "attack_graph_png": str(attack_graph_png),
        "metrics": str(metrics_path),
    }


def _load_demo_dependencies():
    try:
        from src.ingestion.enterprise_log_simulator import save_logs
        from src.models.train_anomaly_model import run_training
        from src.pipeline.trustsphere_pipeline import TrustSpherePipeline
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "TrustSphere demo dependencies are missing in the current Python environment. "
            "Run the demo from the trustsphere-ai virtual environment."
        ) from exc
    return save_logs, run_training, TrustSpherePipeline


def adapt_simulator_event(event: dict[str, Any]) -> NormalizedLog:
    event_type = str(event.get("event_type", "unknown_event")).lower()
    device = str(event.get("device", "unknown-host"))
    status = infer_status(event_type)
    bytes_sent, bytes_received = infer_transfer_sizes(event_type, event.get("label", "normal"))
    return NormalizedLog.model_validate(
        {
            "schema_version": "log.v1",
            "timestamp": event["timestamp"],
            "user": str(event.get("user", "unknown-user")),
            "host": device,
            "ip": str(event.get("ip", "0.0.0.0")),
            "event_type": event_type,
            "status": status,
            "device_type": device.split("-")[0] if "-" in device else device,
            "location": str(event.get("department", "unknown")),
            "process_name": infer_process_name(event),
            "failed_attempts": infer_failed_attempts(event_type, event.get("label", "normal")),
            "bytes_sent": float(bytes_sent),
            "bytes_received": float(bytes_received),
            "login_success": infer_login_success(event_type),
            "event_id": build_event_id(event),
        }
    )


def needs_training() -> bool:
    required = [
        SAVED_MODELS_DIR / "model_iforest.pkl",
        SAVED_MODELS_DIR / "scaler.pkl",
        SAVED_MODELS_DIR / "feature_columns.json",
    ]
    return any(not path.exists() for path in required)


def infer_status(event_type: str) -> str:
    if "failed" in event_type:
        return "failed"
    if event_type in {"data_exfiltration", "privilege_escalation", "lateral_movement", "mass_file_access"}:
        return "alert"
    if event_type in {"logout", "logoff"}:
        return "closed"
    return "success"


def infer_login_success(event_type: str) -> bool | None:
    if "failed" in event_type:
        return False
    if "login" in event_type or event_type in {"logon", "vpn_connect"}:
        return True
    return None


def infer_failed_attempts(event_type: str, label: str) -> int:
    if "failed" in event_type:
        return 6 if label == "attack" else 3
    if event_type == "login_after_hours":
        return 2
    return 0


def infer_transfer_sizes(event_type: str, label: str) -> tuple[int, int]:
    if event_type == "data_exfiltration":
        return 850000, 22000
    if event_type in {"mass_file_access", "file_download"}:
        return 125000 if label != "normal" else 54000, 64000
    if event_type in {"db_query", "file_access", "data_access"}:
        return 18000, 42000
    if event_type in {"email_send", "email_read", "phishing_email"}:
        return 8000, 12000
    if event_type in {"process_execution", "privilege_escalation", "lateral_movement"}:
        return 28000, 18000
    return 2500, 5000


def infer_process_name(event: dict[str, Any]) -> str:
    event_type = str(event.get("event_type", "unknown_event")).lower()
    mapping = {
        "login_success": "winlogon.exe",
        "login_after_hours": "winlogon.exe",
        "login_from_new_ip": "vpnclient.exe",
        "unknown_device_login": "identity-agent.exe",
        "logout": "userinit.exe",
        "file_access": "explorer.exe",
        "mass_file_access": "robocopy.exe",
        "email_send": "outlook.exe",
        "email_read": "outlook.exe",
        "phishing_email": "outlook.exe",
        "process_execution": "powershell.exe",
        "privilege_escalation": "powershell.exe",
        "lateral_movement": "psexec.exe",
        "data_exfiltration": "scp.exe",
        "db_query": "sqlcmd.exe",
        "system_usage": "browser.exe",
        "admin_console_access": "mmc.exe",
        "vpn_connect": "vpnclient.exe",
    }
    source = str(event.get("event_source", "edr")).lower()
    return mapping.get(event_type, f"{source}.exe")


def build_event_id(event: dict[str, Any]) -> str:
    session_id = str(event.get("session_id", "session"))
    event_type = str(event.get("event_type", "event")).lower()
    timestamp = str(event.get("timestamp", "")).replace(":", "").replace("-", "")
    return f"{session_id}-{event_type}-{timestamp[-6:]}"


def export_attack_graph_png(graph_payload: dict[str, Any], output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not MATPLOTLIB_AVAILABLE:
        output_path.write_bytes(base64.b64decode(PLACEHOLDER_PNG))
        return False

    graph = nx.MultiDiGraph()
    for node in graph_payload.get("nodes", []):
        attrs = dict(node)
        node_id = attrs.pop("id")
        graph.add_node(node_id, **attrs)
    for edge in graph_payload.get("edges", []):
        attrs = dict(edge)
        source = attrs.pop("source")
        target = attrs.pop("target")
        key = attrs.pop("edge_key", None)
        graph.add_edge(source, target, key=key, **attrs)

    plt.figure(figsize=(16, 10))
    position = nx.spring_layout(graph, seed=42, k=1.1)
    node_colors = []
    for _, attrs in graph.nodes(data=True):
        risk_level = str(attrs.get("risk_level", "LOW")).upper()
        node_type = str(attrs.get("node_type", "entity"))
        if node_type == "alert":
            node_colors.append({"CRITICAL": "#ff4d6d", "HIGH": "#ff8c42", "MEDIUM": "#f7b801", "LOW": "#4fd1c5"}.get(risk_level, "#4fd1c5"))
        else:
            node_colors.append("#7f5af0")

    nx.draw_networkx_nodes(graph, position, node_color=node_colors, node_size=900, alpha=0.92)
    nx.draw_networkx_edges(graph, position, arrows=True, arrowstyle="-|>", width=1.2, edge_color="#94a3b8", alpha=0.6)
    labels = {}
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("node_type") == "alert":
            labels[node_id] = str(attrs.get("event_type", node_id))[:16]
        else:
            labels[node_id] = str(attrs.get("entity_id", node_id))[:16]
    nx.draw_networkx_labels(graph, position, labels=labels, font_size=7, font_color="#e6edf3")
    plt.title("TrustSphere Attack Graph", color="#ffffff", fontsize=18)
    plt.gca().set_facecolor("#0D1117")
    plt.gcf().patch.set_facecolor("#0D1117")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, facecolor="#0D1117", bbox_inches="tight")
    plt.close()
    return True


def build_metrics_payload(
    raw_logs: list[dict[str, Any]],
    normalized_logs: list[NormalizedLog],
    incident_report: dict[str, Any],
    timings: dict[str, float],
    training_metrics: dict[str, Any],
    graph_rendered: bool,
) -> dict[str, Any]:
    anomaly_results = incident_report.get("anomaly_results", [])
    risk_results = incident_report.get("risk_results", [])
    attack_graph = incident_report.get("attack_graph", {})
    label_counts = pd.Series([event.get("label", "unknown") for event in raw_logs]).value_counts().to_dict()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "incident_report": str(OUTPUTS_DIR / "incident_report.json"),
            "attack_graph_png": str(OUTPUTS_DIR / "attack_graph.png"),
            "metrics": str(OUTPUTS_DIR / "metrics.json"),
        },
        "simulator": {
            "raw_event_count": len(raw_logs),
            "normalized_event_count": len(normalized_logs),
            "label_distribution": label_counts,
        },
        "ueba": {
            "anomaly_entities": len(anomaly_results),
            "max_anomaly_score": max((float(item.get("anomaly_score", 0.0)) for item in anomaly_results), default=0.0),
            "critical_risk_entities": sum(1 for item in risk_results if str(item.get("risk_level", "")).upper() == "CRITICAL"),
            "training_metrics": training_metrics.get("metrics", training_metrics),
        },
        "attack_graph": {
            "node_count": len(attack_graph.get("nodes", [])),
            "edge_count": len(attack_graph.get("edges", [])),
            "chain_count": len(attack_graph.get("chains", [])),
            "critical_chains": int(attack_graph.get("critical_chains", 0)),
            "rendered_with_matplotlib": graph_rendered,
        },
        "soc": {
            "incident_id": incident_report.get("incident_id"),
            "severity": incident_report.get("severity"),
            "confidence": incident_report.get("confidence"),
            "summary_keys": sorted((incident_report.get("incident_summary") or {}).keys()),
        },
        "timings": timings,
        "total_runtime_seconds": round(sum(timings.values()), 4),
    }


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(OUTPUTS_DIR / "trustsphere_demo.log"),
            logging.StreamHandler(),
        ],
    )


if __name__ == "__main__":
    outputs = run_demo()
    print(json.dumps(outputs, indent=2))
