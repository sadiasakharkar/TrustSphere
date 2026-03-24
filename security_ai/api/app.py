"""Unified FastAPI inference platform for TrustSphere."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
import time
from typing import Any

from pydantic import BaseModel, ValidationError

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.exceptions import RequestValidationError
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except Exception:
    FastAPI = None
    HTTPException = Exception
    RequestValidationError = Exception
    Request = object
    Response = object
    CORSMiddleware = object
    JSONResponse = object

from security_ai.api.model_loader import ModelLoader
from security_ai.api.services import DetectorService
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

if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI Platform", version="2.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    loader = ModelLoader.get_instance()
    services = DetectorService(loader)
    soc_service = SOCService()
    registry = MLflowRegistry(base_dir=__import__("pathlib").Path(__file__).resolve().parents[1])
    request_schema_registry = {
        "/detect/email": (EMAIL_REQUEST_SCHEMA_VERSION, EmailDetectionRequest),
        "/detect/url": (URL_REQUEST_SCHEMA_VERSION, URLDetectionRequest),
        "/detect/credential": (CREDENTIAL_REQUEST_SCHEMA_VERSION, CredentialDetectionRequest),
        "/detect/attachment": (ATTACHMENT_REQUEST_SCHEMA_VERSION, AttachmentDetectionRequest),
        "/guard/prompt": (PROMPT_GUARD_REQUEST_SCHEMA_VERSION, PromptGuardRequest),
        "/analyze/incident": (INCIDENT_SCHEMA_VERSION, IncidentAnalysisRequest),
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
        if not body:
            return error_response(
                status_code=422,
                message="Request body is required.",
                meta={"requestId": request_id},
            )
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
        try:
            loader.warmup()
        except Exception as exc:
            LOGGER.warning("Model warmup failed; continuing in resilient mode: %s", exc)
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

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return build_success_payload(
            data={"status": "ok", "service": "trustsphere-security-platform", "async_inference": True, "offline_capable": True}
        )

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_payload()
        return Response(content=payload, media_type=content_type)

    @app.post("/detect/email")
    async def detect_email(request: EmailDetectionRequest):
        result = await services.detect_email(request.model_dump())
        return success_response(result)

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
        return success_response(soc_service.get_overview_summary())

    @app.get("/api/metrics/soc")
    async def soc_metrics():
        return success_response(soc_service.get_soc_metrics())

    @app.get("/api/events/live")
    async def live_events():
        events = soc_service.get_live_events()
        return success_response(events, meta={"count": len(events)})

    @app.get("/api/detections/feed")
    async def detections_feed():
        feed = soc_service.get_detection_feed()
        return success_response(feed, meta={"count": len(feed)})

    @app.get("/api/incidents")
    async def incidents():
        rows = soc_service.list_incidents()
        return success_response(rows, meta={"count": len(rows)})

    @app.get("/api/incidents/{incident_id}")
    async def incident_detail(incident_id: str):
        incident = soc_service.get_incident(incident_id)
        if incident is None:
            return success_response(soc_service.incident_detail_mock(incident_id), meta={"incidentId": incident_id, "fallback": True})
        return success_response(incident)

    @app.patch("/api/incidents/{incident_id}/status")
    async def update_incident_status(incident_id: str, request: IncidentStatusUpdateRequest):
        incident = soc_service.update_incident_status(incident_id, request.status)
        if incident is None:
            return success_response(soc_service.incident_detail_mock(incident_id).get("summary", {}), meta={"incidentId": incident_id, "fallback": True})
        return success_response(incident, meta={"message": "Incident status updated."})

    @app.patch("/api/incidents/{incident_id}/assign")
    async def assign_incident(incident_id: str, request: IncidentAssignmentRequest):
        incident = soc_service.assign_incident(incident_id, request.assignee)
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
        return success_response(soc_service.get_attack_graph())

    @app.get("/api/attack-graph/{incident_id}")
    async def incident_attack_graph(incident_id: str):
        return success_response(soc_service.get_attack_graph(incident_id=incident_id))

    @app.get("/api/playbooks")
    async def playbooks():
        rows = soc_service.list_playbooks()
        return success_response(rows, meta={"count": len(rows)})

    @app.post("/api/playbooks/run")
    async def run_playbook(request: PlaybookRunRequest):
        result = soc_service.run_playbook(incident_id=request.incidentId, playbook_id=request.playbookId)
        return success_response(result, meta={"message": "Playbook prepared for execution."})

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

    @app.get("/api/insights/workflow/{view}")
    async def workflow_insight(view: str, incident_id: str | None = None):
        return success_response(soc_service.get_workflow_insight(view=view, incident_id=incident_id))

    @app.get("/api/insights/incident/{incident_id}")
    async def incident_insight(incident_id: str):
        return success_response(soc_service.get_workflow_insight(view="incident-detail", incident_id=incident_id))
else:
    app = None
