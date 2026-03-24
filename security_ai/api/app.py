"""Unified FastAPI inference platform for TrustSphere."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
import time
from typing import Any

from pydantic import ValidationError

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
    client_identity,
    ensure_request_id,
    error_response,
    rate_limiter,
    read_json_body,
    structured_log,
)
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

if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI Platform", version="2.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    loader = ModelLoader.get_instance()
    services = DetectorService(loader)
    registry = MLflowRegistry(base_dir=__import__("pathlib").Path(__file__).resolve().parents[1])
    request_schema_registry = {
        "/detect/email": (EMAIL_REQUEST_SCHEMA_VERSION, EmailDetectionRequest),
        "/detect/url": (URL_REQUEST_SCHEMA_VERSION, URLDetectionRequest),
        "/detect/credential": (CREDENTIAL_REQUEST_SCHEMA_VERSION, CredentialDetectionRequest),
        "/detect/attachment": (ATTACHMENT_REQUEST_SCHEMA_VERSION, AttachmentDetectionRequest),
        "/guard/prompt": (PROMPT_GUARD_REQUEST_SCHEMA_VERSION, PromptGuardRequest),
        "/analyze/incident": (INCIDENT_SCHEMA_VERSION, IncidentAnalysisRequest),
    }

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
            return error_response(
                status_code=getattr(exc, "status_code", 500),
                error_code="http_error",
                message=str(getattr(exc, "detail", "Unhandled HTTP exception")),
                request_id=request_id,
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
            return error_response(
                status_code=500,
                error_code="internal_error",
                message="Internal server error",
                request_id=request_id,
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
                error_code="rate_limit_exceeded",
                message="Rate limit exceeded.",
                request_id=request_id,
                details={"retry_after_seconds": retry_after},
            )

        if request.method.upper() != "POST":
            return await call_next(request)

        declared_size = int(request.headers.get("content-length", "0") or 0)
        if declared_size > MAX_REQUEST_SIZE_BYTES:
            return error_response(
                status_code=413,
                error_code="request_too_large",
                message=f"Request body exceeds {MAX_REQUEST_SIZE_BYTES} bytes.",
                request_id=request_id,
            )

        body = await request.body()
        if not body:
            return error_response(
                status_code=422,
                error_code="empty_body",
                message="Request body is required.",
                request_id=request_id,
            )
        if len(body) > MAX_REQUEST_SIZE_BYTES:
            return error_response(
                status_code=413,
                error_code="request_too_large",
                message=f"Request body exceeds {MAX_REQUEST_SIZE_BYTES} bytes.",
                request_id=request_id,
            )
        try:
            payload = read_json_body(body)
        except json.JSONDecodeError as exc:
            return error_response(
                status_code=422,
                error_code="invalid_json",
                message=f"Invalid JSON payload: {exc.msg}",
                request_id=request_id,
            )

        if endpoint in request_schema_registry:
            expected_version, schema_model = request_schema_registry[endpoint]
            if payload.get("schema_version") != expected_version:
                return error_response(
                    status_code=422,
                    error_code="invalid_schema_version",
                    message=f"Unsupported schema_version for {endpoint}. Expected {expected_version}.",
                    request_id=request_id,
                )
            try:
                schema_model.model_validate(payload)
            except ValidationError as exc:
                return error_response(
                    status_code=422,
                    error_code="schema_validation_failed",
                    message=f"Request schema validation failed for {endpoint}.",
                    request_id=request_id,
                    details=exc.errors(),
                )

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(
            status_code=422,
            error_code="request_validation_failed",
            message="Request validation failed.",
            request_id=getattr(request.state, "request_id", None),
            details=exc.errors(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        return error_response(
            status_code=422,
            error_code="validation_failed",
            message="Validation failed.",
            request_id=getattr(request.state, "request_id", None),
            details=exc.errors(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_response(
            status_code=getattr(exc, "status_code", 500),
            error_code="http_exception",
            message=str(getattr(exc, "detail", "HTTP exception")),
            request_id=getattr(request.state, "request_id", None),
        )

    @app.on_event("startup")
    async def startup_event() -> None:
        loader.warmup()
        registry.register_model("ueba_anomaly_model", {"component": "trustsphere-ai", "status": "production"})
        registry.register_model("email_detector", {"endpoint": "/detect/email", "status": "production"})
        registry.register_model("url_detector", {"endpoint": "/detect/url", "status": "production"})
        registry.register_model("credential_detector", {"endpoint": "/detect/credential", "status": "production"})
        registry.register_model("attachment_detector", {"endpoint": "/detect/attachment", "status": "production"})
        registry.register_model("prompt_guard", {"endpoint": "/guard/prompt", "status": "production"})
        registry.register_model("incident_analyst", {"endpoint": "/analyze/incident", "status": "production"})
        for detector in ["email", "url", "credential", "attachment", "prompt_guard"]:
            record_model_snapshot(MetricsSnapshot(detector=detector))

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "service": "trustsphere-security-platform", "async_inference": True, "offline_capable": True}

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_payload()
        return Response(content=payload, media_type=content_type)

    @app.post("/detect/email")
    async def detect_email(request: EmailDetectionRequest):
        return await services.detect_email(request.model_dump())

    @app.post("/detect/url")
    async def detect_url(request: URLDetectionRequest):
        return await services.detect_url(request.model_dump())

    @app.post("/detect/credential")
    async def detect_credential(request: CredentialDetectionRequest):
        return await services.detect_credential(request.model_dump())

    @app.post("/detect/attachment")
    async def detect_attachment(request: AttachmentDetectionRequest):
        return await services.detect_attachment(request.model_dump())

    @app.post("/guard/prompt")
    async def guard_prompt(request: PromptGuardRequest):
        return await services.guard_prompt(request.model_dump())

    @app.post("/analyze/incident")
    async def analyze_incident(request: IncidentAnalysisRequest) -> IncidentReport:
        return await services.analyze_incident(request.model_dump())
else:
    app = None
