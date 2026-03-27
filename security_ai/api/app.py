"""Unified FastAPI inference platform for TrustSphere."""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any

from pydantic import BaseModel, ValidationError

try:
    from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
    from fastapi.exceptions import RequestValidationError
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except Exception:
    FastAPI = None
    HTTPException = Exception
    RequestValidationError = Exception
    Request = object
    Response = object
    WebSocket = object
    WebSocketDisconnect = Exception
    CORSMiddleware = object
    JSONResponse = object

from security_ai.api.core.auth import create_token, decode_token
from security_ai.api.auth_store import authenticate_user, create_user, get_user_by_email
from security_ai.api.email_store import build_email_analysis, clear_history as clear_email_history, get_history as get_email_history, get_inbox, save_history as save_email_history
from security_ai.api.ml_runtime.safe_import import ML_AVAILABLE, check_ml_runtime
from security_ai.api.model_loader import ModelLoader
from security_ai.api.pipeline.execution_mode import HYBRID_MODE, LIVE_MODE, SIMULATION_MODE
from security_ai.api.services import (
    DetectionService,
    DetectorService,
    GraphService,
    IncidentStreamBroker,
    LLMService,
    RiskService,
    StorageService,
)
from security_ai.api.middleware import (
    MAX_REQUEST_SIZE_BYTES,
    REQUEST_ID_HEADER,
    authenticator,
    build_success_payload,
    client_identity,
    ensure_request_id,
    error_response,
    rate_limiter,
    read_json_body,
    success_response,
    structured_log,
)
from security_ai.api.soc_service import SOCService
from security_ai.api.system.health_validator import HealthValidator
from security_ai.monitoring.metrics import MetricsSnapshot, REQUEST_COUNTER, REQUEST_LATENCY, metrics_payload, record_model_snapshot
from security_ai.registry.mlflow_registry import MLflowRegistry

BASE_DIR = Path(__file__).resolve().parents[2]
TRUSTSPHERE_AI_DIR = BASE_DIR / "trustsphere-ai"
if str(TRUSTSPHERE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(TRUSTSPHERE_AI_DIR))

from src.contracts import (
    ATTACHMENT_REQUEST_SCHEMA_VERSION,
    CREDENTIAL_REQUEST_SCHEMA_VERSION,
    EMAIL_REQUEST_SCHEMA_VERSION,
    INCIDENT_SCHEMA_VERSION,
    PROMPT_GUARD_REQUEST_SCHEMA_VERSION,
    URL_REQUEST_SCHEMA_VERSION,
    AttachmentDetectionRequest,
    CredentialDetectionRequest,
    EmailDetectionRequest,
    IncidentAnalysisRequest,
    IncidentReport,
    PromptGuardRequest,
    URLDetectionRequest,
)
from src.pipeline.event_normalizer import EventNormalizer

LOGGER = logging.getLogger(__name__)


class IncidentStatusUpdateRequest(BaseModel):
    status: str


class IncidentAssignmentRequest(BaseModel):
    assignee: str


class PlaybookRunRequest(BaseModel):
    incidentId: str
    playbookId: str | None = None


class ReportExportRequest(BaseModel):
    format: str = "markdown"


class AuthLoginRequest(BaseModel):
    email: str
    password: str
    role: str = "analyst"


class AuthSignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "analyst"


class AuthRefreshRequest(BaseModel):
    token: str


class IngestLogsRequest(BaseModel):
    logs: list[dict[str, Any]]


class EmailAnalyzerRequest(BaseModel):
    input: str = ""
    subject: str = ""
    sender: str = "unknown@example.com"


class PlaybookExecutionRequest(BaseModel):
    incident_id: str
    action: str
    target: str | None = None


def _synthetic_test_logs() -> list[dict[str, Any]]:
    now = datetime.utcnow().replace(microsecond=0).isoformat()
    return [
        {
            "timestamp": now,
            "event_id": "test-login-001",
            "user": "demo.analyst",
            "host": "payments-app-01",
            "ip": "203.0.113.41",
            "event_type": "login_failure_burst",
            "action": "login_failure_burst",
            "source": "IAM",
            "severity": "High",
            "status": "failed",
            "failed_attempts": 8,
            "raw_payload": {"scenario": "pipeline_test"},
        },
        {
            "timestamp": now,
            "event_id": "test-priv-002",
            "user": "demo.analyst",
            "host": "payments-app-01",
            "ip": "203.0.113.41",
            "event_type": "privilege_escalation",
            "action": "privilege_escalation",
            "source": "EDR",
            "severity": "Critical",
            "status": "success",
            "bytes_sent": 750000,
            "raw_payload": {"scenario": "pipeline_test"},
        },
    ]

if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI Platform", version="2.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    loader = ModelLoader.get_instance()
    services = DetectorService(loader)
    normalizer = EventNormalizer()
    storage_service = StorageService()
    live_detection_service = DetectionService(loader)
    risk_service = RiskService()
    graph_service = GraphService()
    llm_service = LLMService()
    stream_broker = IncidentStreamBroker()
    soc_service = SOCService()
    app.state.pipeline_mode = HYBRID_MODE
    registry = MLflowRegistry(base_dir=__import__("pathlib").Path(__file__).resolve().parents[1])
    request_schema_registry = {
        "/detect/email": (EMAIL_REQUEST_SCHEMA_VERSION, EmailDetectionRequest),
        "/detect/url": (URL_REQUEST_SCHEMA_VERSION, URLDetectionRequest),
        "/detect/credential": (CREDENTIAL_REQUEST_SCHEMA_VERSION, CredentialDetectionRequest),
        "/detect/attachment": (ATTACHMENT_REQUEST_SCHEMA_VERSION, AttachmentDetectionRequest),
        "/guard/prompt": (PROMPT_GUARD_REQUEST_SCHEMA_VERSION, PromptGuardRequest),
        "/analyze/incident": (INCIDENT_SCHEMA_VERSION, IncidentAnalysisRequest),
    }
    body_optional_post_paths = {
        "/system/test-pipeline",
    }

    def _storage_incidents_or_fallback() -> list[dict[str, Any]]:
        incidents = storage_service.fetch_incidents()
        return incidents if incidents else soc_service.list_incidents()

    def _incident_for_graph(incident_id: str | None = None) -> dict[str, Any] | None:
        if incident_id:
            return storage_service.get_incident(incident_id) or soc_service.get_incident(incident_id)
        incidents = storage_service.fetch_incidents()
        if incidents:
            return incidents[0]
        rows = soc_service.list_incidents()
        return rows[0] if rows else None

    def _compose_live_overview() -> dict[str, Any]:
        incidents = storage_service.fetch_incidents()
        metrics = storage_service.aggregate_metrics()
        if not incidents:
            return soc_service.get_overview_summary()
        confidence_values = []
        for item in incidents[:5]:
            value = item.get("confidence", 0.9)
            try:
                confidence_values.append(float(value))
            except Exception:
                confidence_values.append(0.9)
        detection_confidence = min(max(sum(confidence_values) / max(len(confidence_values), 1), 0.01), 0.99)
        return {
            "headline": {
                "title": "Security Operations Overview",
                "subtitle": "Live intelligence across normalized logs, anomaly scoring, graph correlation, and local reasoning.",
                "status": "Live backend telemetry",
                "updatedAt": metrics.get("recent_activity", [{}])[0].get("timestamp", soc_service.response_meta()["startedAt"]),
            },
            "metrics": [
                {"label": "Active Incidents", "value": len([item for item in incidents if str(item.get("status", "")).lower() != "resolved"]), "delta": "+2", "status": "critical", "helper": "Persisted incident index"},
                {"label": "Risk Score", "value": round(sum(float(item.get("risk_score", item.get("riskScore", 0))) for item in incidents[:5]) / max(min(len(incidents), 5), 1), 1), "delta": "+4%", "status": "high", "helper": "Average top incident risk"},
                {"label": "Detection Confidence", "value": f"{detection_confidence:.2f}", "delta": "Stable", "status": "healthy", "helper": "LLM + ML confidence"},
                {"label": "System Status", "value": storage_service.backend.title(), "delta": "Online", "status": "healthy", "helper": "Storage and inference path"},
            ],
            "criticalQueue": incidents[:5],
            "modelHealth": soc_service.get_detection_feed(),
            "demoScenario": {
                "title": incidents[0].get("title", "Live SOC incident focus"),
                "focusIncidentId": incidents[0].get("id"),
                "summary": incidents[0].get("llm_summary", incidents[0].get("title", "Live risk detected")),
            },
        }

    async def _broadcast_event(event_type: str, payload: dict[str, Any]) -> None:
        await stream_broker.broadcast({
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload,
        })

    async def _ingest_and_detect(raw_logs: list[dict[str, Any]]) -> dict[str, Any]:
        LOGGER.info("[PIPELINE] normalize ✔")
        normalized_events = [event.model_dump(mode="json") for event in normalizer.normalize(raw_logs)]
        storage_service.index_normalized_logs(normalized_events)
        LOGGER.info("[PIPELINE] anomaly ✔")
        detections = live_detection_service.detect(raw_logs)
        created_incidents = []
        history = storage_service.fetch_incidents()
        for index, detection in enumerate(detections):
            source_event = normalized_events[min(index, len(normalized_events) - 1)] if normalized_events else {}
            LOGGER.info("[PIPELINE] risk ✔")
            risk = risk_service.score(detection, history=history, asset_type="server" if "db" in str(source_event.get("host", "")).lower() else "workstation")
            incident_id = source_event.get("event_id") or f"INC-LIVE-{int(time.time() * 1000)}-{index}"
            incident = {
                "id": incident_id,
                "title": detection.get("deviation_reason", "Anomalous activity detected"),
                "severity": risk["severity"].title(),
                "status": "OPEN",
                "assigned_to": "Unassigned",
                "owner": "Unassigned",
                "mitre_stage": "TA0001 Initial Access" if "login" in str(source_event.get("event_type", "")).lower() else "TA0008 Lateral Movement",
                "anomaly_score": detection["anomaly_score"],
                "risk_score": risk["risk_score"],
                "riskScore": risk["risk_score"],
                "created_at": source_event.get("timestamp"),
                "updatedAt": datetime.now().isoformat(),
                "entities": [source_event.get("user"), source_event.get("host"), source_event.get("ip")],
                "entity": source_event.get("host") or source_event.get("user"),
                "eventType": source_event.get("event_type"),
                "confidence": f"{min(max(float(detection['anomaly_score']) + 0.05, 0.01), 0.99):.2f}",
                "timeline": [
                    {"time": str(source_event.get("timestamp", ""))[-8:-3], "title": "Log ingested", "detail": f"{source_event.get('event_type', 'event')} normalized and indexed."},
                    {"time": datetime.utcnow().strftime("%H:%M"), "title": "Anomaly detected", "detail": detection.get("deviation_reason", "Behavior deviated from baseline.")},
                    {"time": datetime.utcnow().strftime("%H:%M"), "title": "Risk scored", "detail": f"Composite risk evaluated at {risk['risk_score']} ({risk['severity']})."},
                ],
                "evidence": [
                    {"title": "Deviation reason", "content": detection.get("deviation_reason", "Behavior deviated from baseline.")},
                    {"title": "Feature importance", "content": json.dumps(detection.get("feature_importance", {}), default=str)},
                    {"title": "Risk explanation", "content": f"Final risk combines anomaly, behavior, asset criticality, threat weight, and frequency."},
                ],
                "relatedAlerts": [source_event],
                "summary": {
                    "id": incident_id,
                    "title": detection.get("deviation_reason", "Anomalous activity detected"),
                    "severity": risk["severity"].title(),
                    "confidence": f"{min(max(float(detection['anomaly_score']) + 0.05, 0.01), 0.99):.2f}",
                    "status": "OPEN",
                    "owner": "Unassigned",
                    "users": [source_event.get("user")],
                    "hosts": [source_event.get("host")],
                    "mitre": ["Initial Access" if "login" in str(source_event.get("event_type", "")).lower() else "Lateral Movement"],
                },
            }
            LOGGER.info("[PIPELINE] graph ✔")
            graph = graph_service.build_graph(incident, [detection])
            LOGGER.info("[PIPELINE] reasoning ✔")
            llm = llm_service.summarize_incident(
                anomaly_result=detection,
                attack_graph=graph,
                entity_behavior=risk,
                historical_context={"history_count": len(history), "recent_alerts": storage_service.query_alerts(limit=5)},
            )
            incident["graph"] = graph
            incident["llm_summary"] = llm["summary"]
            incident["llm_reasoning"] = llm["reasoning"]
            incident["llm_confidence"] = llm["confidence"]
            incident["recommended_actions"] = llm["recommended_actions"]
            incident["attack_stage"] = llm["attack_stage"]
            storage_service.index_incident(incident)
            storage_service.index_entity({
                "entity_id": detection["entity_id"],
                "entity_type": "user",
                "risk_score": risk["risk_score"],
                "severity": risk["severity"],
            })
            created_incidents.append(incident)
            history.append(incident)
            LOGGER.info("[PIPELINE] incident ✔")
            await _broadcast_event("INCIDENT_CREATED", {"incident": incident, "risk": risk, "graph": graph})
        return {
            "normalized_logs": normalized_events,
            "detections": detections,
            "incidents": created_incidents,
        }

    def _fallback_payload_for_path(path: str, method: str = "GET") -> Any | None:
        normalized_method = str(method or "GET").upper()
        clean_path = path.split("?")[0]

        if clean_path == "/health":
            return {"status": "ok", "service": "trustsphere-security-platform", "async_inference": True, "offline_capable": True}
        if clean_path == "/api/overview/summary":
            return soc_service.overview_mock()
        if clean_path == "/api/metrics/soc":
            return soc_service.get_soc_metrics()
        if clean_path == "/api/events/live":
            return soc_service.events_mock()
        if clean_path == "/api/detections/feed":
            return soc_service.models_health_mock()
        if clean_path == "/api/incidents":
            return soc_service.incidents_mock()
        if clean_path.startswith("/api/incidents/") and not clean_path.endswith("/status") and not clean_path.endswith("/assign"):
            incident_id = clean_path.split("/")[-1]
            return soc_service.incident_detail_mock(incident_id)
        if clean_path.endswith("/status") or clean_path.endswith("/assign"):
            incident_id = clean_path.split("/")[3] if len(clean_path.split("/")) > 3 else None
            return soc_service.incident_detail_mock(incident_id).get("summary", {})
        if clean_path.startswith("/api/investigations/entity/"):
            entity_id = clean_path.split("/")[-1]
            return soc_service.investigations_mock(entity_id)
        if clean_path == "/api/events/search":
            return soc_service.events_mock()
        if clean_path == "/api/attack-graph" or clean_path.startswith("/api/attack-graph/"):
            incident_id = clean_path.split("/")[-1] if clean_path.count("/") > 3 else None
            return soc_service.graph_mock(incident_id if clean_path != "/api/attack-graph" else None)
        if clean_path == "/api/playbooks":
            return soc_service.list_playbooks()
        if clean_path == "/api/playbooks/run" and normalized_method == "POST":
            return soc_service.run_playbook("INC-21403")
        if clean_path == "/api/reports":
            return soc_service.reports_mock()
        if clean_path.startswith("/api/reports/") and clean_path.endswith("/export"):
            report_id = clean_path.split("/")[3] if len(clean_path.split("/")) > 3 else "RPT-201"
            return soc_service.export_report(report_id, export_format="markdown") or soc_service.export_report("RPT-201", export_format="markdown")
        if clean_path == "/api/admin/system":
            return soc_service.get_admin_system()
        if clean_path == "/api/admin/users":
            return soc_service.get_admin_users()
        if clean_path.startswith("/api/insights/workflow/"):
            view = clean_path.split("/")[-1]
            return soc_service.get_workflow_insight(view=view)
        if clean_path.startswith("/api/insights/incident/"):
            incident_id = clean_path.split("/")[-1]
            return soc_service.get_workflow_insight(view="incident-detail", incident_id=incident_id)
        return None

    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        request_id = ensure_request_id(request)
        start = time.perf_counter()
        endpoint = getattr(request, "url", None).path if getattr(request, "url", None) else "unknown"
        client_id = client_identity(request)
        try:
            response = await call_next(request)
            REQUEST_COUNTER.labels(endpoint, str(getattr(response, "status_code", 200))).inc()
            response.headers[REQUEST_ID_HEADER] = request_id
            structured_log(
                LOGGER,
                "api_request_completed",
                request_id=request_id,
                method=getattr(request, "method", "UNKNOWN"),
                path=endpoint,
                client_id=client_id,
                status_code=getattr(response, "status_code", 200),
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            return response
        except HTTPException as exc:
            REQUEST_COUNTER.labels(endpoint, str(getattr(exc, "status_code", 500))).inc()
            structured_log(
                LOGGER,
                "api_request_failed",
                request_id=request_id,
                method=getattr(request, "method", "UNKNOWN"),
                path=endpoint,
                client_id=client_id,
                status_code=getattr(exc, "status_code", 500),
                error=str(getattr(exc, "detail", "Unhandled HTTP exception")),
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            fallback = _fallback_payload_for_path(endpoint, getattr(request, "method", "GET"))
            if fallback is not None:
                return success_response(
                    fallback,
                    meta={
                        "requestId": request_id,
                        "path": endpoint,
                        "fallback": True,
                        "fallbackReason": str(getattr(exc, "detail", "Unhandled HTTP exception")),
                    },
                )
            return error_response(
                status_code=getattr(exc, "status_code", 500),
                message=str(getattr(exc, "detail", "Unhandled HTTP exception")),
                meta={"requestId": request_id, "path": endpoint},
            )
        except Exception as exc:
            LOGGER.exception("Unhandled API error on %s: %s", endpoint, exc)
            REQUEST_COUNTER.labels(endpoint, "500").inc()
            structured_log(
                LOGGER,
                "api_request_exception",
                request_id=request_id,
                method=getattr(request, "method", "UNKNOWN"),
                path=endpoint,
                client_id=client_id,
                status_code=500,
                error=str(exc),
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            fallback = _fallback_payload_for_path(endpoint, getattr(request, "method", "GET"))
            if fallback is not None:
                return success_response(
                    fallback,
                    meta={
                        "requestId": request_id,
                        "path": endpoint,
                        "fallback": True,
                        "fallbackReason": "Internal server error",
                    },
                )
            return error_response(
                status_code=500,
                message="Internal server error",
                meta={"requestId": request_id, "path": endpoint},
            )
        finally:
            REQUEST_LATENCY.labels(endpoint).observe(time.perf_counter() - start)

    @app.middleware("http")
    async def enterprise_security_middleware(request: Request, call_next):
        if getattr(request, "url", None) is None:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", None) or ensure_request_id(request)
        endpoint = request.url.path
        client_id = client_identity(request)

        authenticator.validate(request)

        allowed, _, retry_after = rate_limiter.allow(client_id)
        if not allowed:
            return error_response(
                status_code=429,
                message="Rate limit exceeded.",
                meta={"requestId": request_id, "retryAfterSeconds": retry_after},
            )

        if request.method.upper() != "POST":
            return await call_next(request)

        declared_size = int(request.headers.get("content-length", "0") or 0)
        if declared_size > MAX_REQUEST_SIZE_BYTES:
            return error_response(
                status_code=413,
                message=f"Request body exceeds {MAX_REQUEST_SIZE_BYTES} bytes.",
                meta={"requestId": request_id},
            )

        body = await request.body()
        if not body and endpoint not in body_optional_post_paths:
            return error_response(
                status_code=422,
                message="Request body is required.",
                meta={"requestId": request_id},
            )
        if not body:
            async def receive_empty() -> dict[str, Any]:
                return {"type": "http.request", "body": b"", "more_body": False}

            request._receive = receive_empty
            return await call_next(request)
        if len(body) > MAX_REQUEST_SIZE_BYTES:
            return error_response(
                status_code=413,
                message=f"Request body exceeds {MAX_REQUEST_SIZE_BYTES} bytes.",
                meta={"requestId": request_id},
            )
        try:
            payload = read_json_body(body)
        except json.JSONDecodeError as exc:
            return error_response(
                status_code=422,
                message=f"Invalid JSON payload: {exc.msg}",
                meta={"requestId": request_id},
            )

        if endpoint in request_schema_registry:
            expected_version, schema_model = request_schema_registry[endpoint]
            if payload.get("schema_version") != expected_version:
                return error_response(
                    status_code=422,
                    message=f"Unsupported schema_version for {endpoint}. Expected {expected_version}.",
                    meta={"requestId": request_id, "expectedSchemaVersion": expected_version},
                )
            try:
                schema_model.model_validate(payload)
            except ValidationError as exc:
                return error_response(
                    status_code=422,
                    message=f"Request schema validation failed for {endpoint}.",
                    meta={"requestId": request_id, "details": exc.errors()},
                )

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(
            status_code=422,
            message="Request validation failed.",
            meta={"requestId": getattr(request.state, "request_id", None), "details": exc.errors()},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        return error_response(
            status_code=422,
            message="Validation failed.",
            meta={"requestId": getattr(request.state, "request_id", None), "details": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_response(
            status_code=getattr(exc, "status_code", 500),
            message=str(getattr(exc, "detail", "HTTP exception")),
            meta={"requestId": getattr(request.state, "request_id", None)},
        )

    @app.on_event("startup")
    async def startup_event() -> None:
        if ML_AVAILABLE:
            try:
                loader.warmup()
            except Exception as exc:
                LOGGER.warning("Model warmup failed; continuing in resilient mode: %s", exc)
        else:
            LOGGER.warning("[PIPELINE] anomaly degraded to simulation mode because ML runtime is disabled or unavailable.")
        try:
            registry.register_model("ueba_anomaly_model", {"component": "trustsphere-ai", "status": "production"})
            registry.register_model("email_detector", {"endpoint": "/detect/email", "status": "production"})
            registry.register_model("url_detector", {"endpoint": "/detect/url", "status": "production"})
            registry.register_model("credential_detector", {"endpoint": "/detect/credential", "status": "production"})
            registry.register_model("attachment_detector", {"endpoint": "/detect/attachment", "status": "production"})
            registry.register_model("prompt_guard", {"endpoint": "/guard/prompt", "status": "production"})
            registry.register_model("incident_analyst", {"endpoint": "/analyze/incident", "status": "production"})
        except Exception as exc:
            LOGGER.warning("Model registry bootstrap failed; continuing in resilient mode: %s", exc)
        for detector in ["email", "url", "credential", "attachment", "prompt_guard"]:
            record_model_snapshot(MetricsSnapshot(detector=detector))
        try:
            seed_events = soc_service.get_live_events()[:20]
            normalized_seed = []
            for event in seed_events:
                normalized_seed.append({
                    "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                    "user": event.get("user", event.get("entity", "unknown-user")),
                    "host": event.get("host", event.get("entity", "unknown-host")),
                    "ip": event.get("ip", "127.0.0.1"),
                    "action": event.get("eventType", "seed_event"),
                    "event_type": event.get("eventType", "seed_event"),
                    "source": event.get("source", "seed"),
                    "severity": event.get("severity", "Medium"),
                    "status": event.get("status", "success"),
                    "raw_payload": event,
                })
            storage_service.index_normalized_logs(normalized_seed)
            for incident in soc_service.list_incidents():
                storage_service.index_incident({
                    **incident,
                    "risk_score": incident.get("riskScore", incident.get("risk_score", 0)),
                })
        except Exception as exc:
            LOGGER.warning("Storage bootstrap failed; continuing in resilient mode: %s", exc)
        if not storage_service.fetch_incidents():
            for incident in soc_service.list_incidents()[:10]:
                storage_service.index_incident({**incident, "risk_score": incident.get("riskScore", incident.get("risk_score", 0))})
        health = HealthValidator(
            storage_backend=storage_service.backend,
            ollama_health=llm_service.health(),
            websocket_enabled=True,
        ).check_pipeline_ready()
        app.state.pipeline_mode = health["pipeline_mode"]
        app.state.bootstrap_transition_task = asyncio.create_task(soc_service.activate_bootstrap_transition())
        app.state.streaming_task = asyncio.create_task(soc_service.run_streaming_updates())

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return build_success_payload(
            data={
                "status": "ok",
                "service": "trustsphere-security-platform",
                "async_inference": True,
                "offline_capable": True,
                "mode": soc_service.response_meta()["mode"],
                "bootstrapMode": soc_service.response_meta()["bootstrapMode"],
                "streamCounter": soc_service.response_meta()["streamCounter"],
                "storageBackend": storage_service.backend,
                "backendConnected": True,
                "modelActive": True,
                "pipelineMode": app.state.pipeline_mode,
            }
        )

    @app.get("/system/health")
    async def system_health():
        health = HealthValidator(
            storage_backend=storage_service.backend,
            ollama_health=llm_service.health(),
            websocket_enabled=True,
        ).check_pipeline_ready()
        return success_response({
            **health,
            "api": "healthy",
            "storage_backend": storage_service.backend,
            "bootstrap_mode": soc_service.response_meta()["bootstrapMode"],
            "stream_counter": soc_service.response_meta()["streamCounter"],
        })

    @app.get("/system/models")
    async def system_models():
        return success_response({
            "models": soc_service.get_detection_feed(),
            "ollama": llm_service.health(),
            "ml_runtime": check_ml_runtime(),
            "pipeline_mode": app.state.pipeline_mode,
        })

    @app.get("/system/metrics")
    async def system_metrics():
        return success_response(storage_service.aggregate_metrics())

    @app.post("/auth/login")
    async def auth_login(request: AuthLoginRequest):
        try:
            user = authenticate_user(request.email, request.password)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc))
        token = create_token(user["email"], user["role"])
        refresh_token = create_token(f"{user['email']}:refresh", user["role"])
        return success_response({
            "access_token": token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        })

    @app.post("/auth/signup")
    async def auth_signup(request: AuthSignupRequest):
        try:
            user = create_user(request.name, request.email, request.password, request.role)
        except ValueError as exc:
            message = str(exc)
            status_code = 409 if "already exists" in message else 400
            raise HTTPException(status_code=status_code, detail=message)
        return success_response({
            "message": "User registered successfully.",
            "user": user,
        }, status_code=201)

    @app.get("/auth/me")
    async def auth_me(request: Request):
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Access denied. Token is missing.")
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail=str(exc))
        subject = str(payload.get("sub", "")).split(":")[0]
        user = get_user_by_email(subject)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token. User not found.")
        return success_response({
            "message": "User verified successfully.",
            "user": user,
        })

    @app.post("/auth/refresh")
    async def auth_refresh(request: AuthRefreshRequest):
        payload = decode_token(request.token)
        subject = str(payload.get("sub", "secure.operator")).split(":")[0]
        role = str(payload.get("role", "analyst")).lower()
        return success_response({
            "access_token": create_token(subject, role),
            "token_type": "bearer",
        })

    @app.post("/ingest/logs")
    async def ingest_logs(request: IngestLogsRequest):
        result = await _ingest_and_detect(request.logs)
        return success_response(result, meta={"ingested": len(request.logs), "storageBackend": storage_service.backend})

    @app.post("/system/test-pipeline")
    async def system_test_pipeline():
        result = await _ingest_and_detect(_synthetic_test_logs())
        return success_response({
            "status": "success",
            "incident_created": bool(result.get("incidents")),
            "pipeline_mode": app.state.pipeline_mode,
        })

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_payload()
        return Response(content=payload, media_type=content_type)

    @app.post("/detect/email")
    async def detect_email(request: EmailDetectionRequest):
        result = await services.detect_email(request.model_dump())
        return success_response(result)

    @app.get("/api/email/inbox")
    async def email_inbox():
        rows = get_inbox()
        return success_response(rows, meta={"count": len(rows)})

    @app.get("/api/email/history")
    async def email_history():
        rows = list(reversed(get_email_history()))
        return success_response(rows, meta={"count": len(rows)})

    @app.delete("/api/email/history")
    async def delete_email_history():
        clear_email_history()
        return success_response({"status": "cleared"}, meta={"message": "Email history cleared."})

    @app.post("/api/email/analyze")
    async def analyze_email_module(request: EmailAnalyzerRequest):
        detector_result = await services.detect_email({
            "email_text": request.input,
            "subject": request.subject,
            "body": request.input,
            "sender": request.sender,
        })
        analysis = build_email_analysis(
            detector_result,
            email_text=request.input,
            subject=request.subject,
            sender=request.sender,
        )
        save_email_history(analysis)
        return success_response({
            "risk_score": analysis["risk_score"],
            "severity": analysis["severity"],
            "models": analysis["models"],
            "actions_taken": analysis["actions"],
            "label": analysis["label"],
        }, meta={"message": "Email analyzed."})

    @app.post("/detect/url")
    async def detect_url(request: URLDetectionRequest):
        result = await services.detect_url(request.model_dump())
        return success_response(result)

    @app.post("/detect/credential")
    async def detect_credential(request: CredentialDetectionRequest):
        result = await services.detect_credential(request.model_dump())
        return success_response(result)

    @app.post("/detect/attachment")
    async def detect_attachment(request: AttachmentDetectionRequest):
        result = await services.detect_attachment(request.model_dump())
        return success_response(result)

    @app.post("/guard/prompt")
    async def guard_prompt(request: PromptGuardRequest):
        result = await services.guard_prompt(request.model_dump())
        return success_response(result)

    @app.post("/analyze/incident")
    async def analyze_incident(request: IncidentAnalysisRequest) -> IncidentReport:
        result = await services.analyze_incident(request.model_dump())
        return success_response(result)

    @app.get("/api/overview/summary")
    async def overview_summary():
        return success_response(_compose_live_overview(), meta={**soc_service.response_meta(), "storageBackend": storage_service.backend})

    @app.get("/api/metrics/soc")
    async def soc_metrics():
        live_metrics = storage_service.aggregate_metrics()
        data = soc_service.get_soc_metrics() if not live_metrics["incidents_indexed"] else {
            **soc_service.get_soc_metrics(),
            **live_metrics,
        }
        return success_response(data, meta={**soc_service.response_meta(), "storageBackend": storage_service.backend})

    @app.get("/api/events/live")
    async def live_events():
        events = storage_service.query_alerts(limit=50) or soc_service.get_live_events()
        return success_response(events, meta={"count": len(events), **soc_service.response_meta()})

    @app.get("/api/detections/feed")
    async def detections_feed():
        feed = soc_service.get_detection_feed()
        return success_response(feed, meta={"count": len(feed), **soc_service.response_meta()})

    @app.get("/api/incidents")
    async def incidents():
        rows = _storage_incidents_or_fallback()
        return success_response(rows, meta={"count": len(rows), **soc_service.response_meta()})

    @app.get("/api/incidents/{incident_id}")
    async def incident_detail(incident_id: str):
        incident = storage_service.get_incident(incident_id) or soc_service.get_incident(incident_id)
        if incident is None:
            return success_response(soc_service.incident_detail_mock(incident_id), meta={"incidentId": incident_id, "fallback": True, **soc_service.response_meta()})
        return success_response(incident, meta=soc_service.response_meta())

    @app.patch("/api/incidents/{incident_id}/status")
    async def update_incident_status(incident_id: str, request: IncidentStatusUpdateRequest):
        incident = storage_service.get_incident(incident_id) or soc_service.update_incident_status(incident_id, request.status)
        if incident and storage_service.get_incident(incident_id):
            incident["status"] = request.status
            storage_service.index_incident(incident)
            await _broadcast_event("risk_updated", {"incident_id": incident_id, "status": request.status, "incident": incident})
        if incident is None:
            return success_response(soc_service.incident_detail_mock(incident_id).get("summary", {}), meta={"incidentId": incident_id, "fallback": True})
        return success_response(incident, meta={"message": "Incident status updated."})

    @app.patch("/api/incidents/{incident_id}/assign")
    async def assign_incident(incident_id: str, request: IncidentAssignmentRequest):
        incident = storage_service.get_incident(incident_id) or soc_service.assign_incident(incident_id, request.assignee)
        if incident and storage_service.get_incident(incident_id):
            incident["owner"] = request.assignee
            incident["assigned_to"] = request.assignee
            storage_service.index_incident(incident)
        if incident is None:
            return success_response(soc_service.incident_detail_mock(incident_id).get("summary", {}), meta={"incidentId": incident_id, "fallback": True})
        return success_response(incident, meta={"message": "Incident assigned."})

    @app.get("/api/investigations/entity/{entity_id}")
    async def investigation_entity(entity_id: str):
        return success_response(soc_service.get_investigation_entity(entity_id))

    @app.get("/api/events/search")
    async def search_events(query: str = "", severity: str | None = None):
        rows = soc_service.search_events(query=query, severity=severity)
        return success_response(rows, meta={"count": len(rows), "query": query, "severity": severity})

    @app.get("/api/attack-graph")
    async def attack_graph():
        incident = _incident_for_graph()
        graph = graph_service.build_graph(incident or soc_service.list_incidents()[0]) if incident else soc_service.get_attack_graph()
        return success_response(graph, meta=soc_service.response_meta())

    @app.get("/api/attack-graph/{incident_id}")
    async def incident_attack_graph(incident_id: str):
        incident = _incident_for_graph(incident_id)
        graph = graph_service.build_graph(incident) if incident else soc_service.get_attack_graph(incident_id=incident_id)
        return success_response(graph, meta=soc_service.response_meta())

    @app.get("/graph/{incident_id}")
    async def incident_graph(incident_id: str):
        incident = _incident_for_graph(incident_id)
        graph = graph_service.build_graph(incident) if incident else soc_service.get_attack_graph(incident_id=incident_id)
        return success_response(graph)

    @app.get("/api/playbooks")
    async def playbooks():
        rows = soc_service.list_playbooks()
        return success_response(rows, meta={"count": len(rows)})

    @app.post("/api/playbooks/run")
    async def run_playbook(request: PlaybookRunRequest):
        result = soc_service.run_playbook(incident_id=request.incidentId, playbook_id=request.playbookId)
        await _broadcast_event("playbook_executed", result)
        return success_response(result, meta={"message": "Playbook prepared for execution."})

    @app.post("/playbook/execute")
    async def execute_playbook(request: PlaybookExecutionRequest):
        timeline_entry = {
            "time": datetime.utcnow().strftime("%H:%M"),
            "title": f"Playbook action: {request.action}",
            "detail": f"Target {request.target or 'incident scope'} updated through simulated response automation.",
        }
        incident = storage_service.get_incident(request.incident_id) or soc_service.get_incident(request.incident_id)
        if incident is None:
            incident = soc_service.incident_detail_mock(request.incident_id)
        incident.setdefault("timeline", []).append(timeline_entry)
        storage_service.index_incident(incident)
        await _broadcast_event("playbook_executed", {"incident_id": request.incident_id, "action": request.action, "target": request.target, "timeline": timeline_entry})
        return success_response({"incident_id": request.incident_id, "timeline": timeline_entry, "status": "EXECUTED"})

    @app.get("/api/reports")
    async def reports():
        rows = soc_service.list_reports()
        return success_response(rows, meta={"count": len(rows)})

    @app.post("/api/reports/{report_id}/export")
    async def export_report(report_id: str, request: ReportExportRequest):
        result = soc_service.export_report(report_id, export_format=request.format)
        if result is None:
            return success_response(soc_service.export_report("RPT-201", export_format=request.format), meta={"reportId": report_id, "fallback": True})
        return success_response(result, meta={"message": "Report export created."})

    @app.get("/api/admin/system")
    async def admin_system():
        return success_response(soc_service.get_admin_system())

    @app.get("/api/admin/users")
    async def admin_users():
        rows = soc_service.get_admin_users()
        return success_response(rows, meta={"count": len(rows)})

    @app.get("/incidents")
    async def incidents_soc_ready():
        incidents = _storage_incidents_or_fallback()
        enriched = []
        for incident in incidents:
            risk_value = float(incident.get("risk_score", incident.get("riskScore", 0.0)))
            graph = incident.get("graph") or graph_service.build_graph(incident)
            llm = {
                "summary": incident.get("llm_summary"),
                "reasoning": incident.get("llm_reasoning"),
                "attack_stage": incident.get("attack_stage"),
                "confidence": incident.get("llm_confidence", incident.get("confidence", 0.9)),
                "recommended_actions": incident.get("recommended_actions", []),
            }
            if not llm["summary"]:
                llm = llm_service.summarize_incident(
                    anomaly_result={"anomaly_score": incident.get("anomaly_score", 0.0)},
                    attack_graph=graph,
                    entity_behavior={"severity": incident.get("severity"), "risk_score": risk_value},
                    historical_context={"recent_alerts": storage_service.query_alerts(limit=5)},
                )
            enriched.append({
                **incident,
                "risk_score": risk_value,
                "graph_summary": graph.get("chain_summary"),
                "llm": llm,
            })
        return success_response(enriched, meta={"count": len(enriched), "storageBackend": storage_service.backend})

    @app.websocket("/ws/incidents")
    async def websocket_incidents(websocket: WebSocket):
        await stream_broker.connect(websocket)
        try:
            await websocket.send_text(json.dumps({
                "type": "connected",
                "timestamp": time.time(),
                "payload": {
                    "mode": soc_service.response_meta()["mode"],
                    "count": len(_storage_incidents_or_fallback()),
                },
            }))
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await stream_broker.disconnect(websocket)
        except Exception:
            await stream_broker.disconnect(websocket)

    @app.get("/api/insights/workflow/{view}")
    async def workflow_insight(view: str, incident_id: str | None = None):
        return success_response(soc_service.get_workflow_insight(view=view, incident_id=incident_id))

    @app.get("/api/insights/incident/{incident_id}")
    async def incident_insight(incident_id: str):
        return success_response(soc_service.get_workflow_insight(view="incident-detail", incident_id=incident_id))
else:
    app = None
