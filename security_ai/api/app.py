"""Unified FastAPI inference platform for TrustSphere."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
except Exception:
    FastAPI = None
    HTTPException = Exception
    Request = object
    Response = object
    CORSMiddleware = object

from security_ai.api.model_loader import ModelLoader
from security_ai.api.services import DetectorService
from security_ai.monitoring.metrics import MetricsSnapshot, REQUEST_COUNTER, REQUEST_LATENCY, metrics_payload, record_model_snapshot
from security_ai.registry.mlflow_registry import MLflowRegistry

LOGGER = logging.getLogger(__name__)


class EmailDetectionRequest(BaseModel):
    email_text: str = Field(default="")
    subject: str = Field(default="")
    body: str = Field(default="")
    sender: str = Field(default="unknown@example.com")
    attachments: str = Field(default="")


class URLDetectionRequest(BaseModel):
    url: str


class CredentialDetectionRequest(BaseModel):
    text: str
    commit_message: str = Field(default="")
    paste_context: str = Field(default="")


class AttachmentDetectionRequest(BaseModel):
    filename: str
    size_bytes: int
    content_text: str = Field(default="")
    event_context: str = Field(default="")
    post_download_action: str = Field(default="")


class IncidentAnalysisRequest(BaseModel):
    summary: str = Field(default="")
    severity: str = Field(default="LOW")
    indicators: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    logs: list[dict[str, Any]] = Field(default_factory=list)


class PromptGuardRequest(BaseModel):
    prompt: str


if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI Platform", version="2.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    loader = ModelLoader.get_instance()
    services = DetectorService(loader)
    registry = MLflowRegistry(base_dir=__import__("pathlib").Path(__file__).resolve().parents[1])

    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        start = time.perf_counter()
        endpoint = getattr(request, "url", None).path if getattr(request, "url", None) else "unknown"
        try:
            response = await call_next(request)
            REQUEST_COUNTER.labels(endpoint, str(getattr(response, "status_code", 200))).inc()
            return response
        except Exception as exc:
            LOGGER.exception("Unhandled API error on %s: %s", endpoint, exc)
            REQUEST_COUNTER.labels(endpoint, "500").inc()
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            REQUEST_LATENCY.labels(endpoint).observe(time.perf_counter() - start)

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
    async def analyze_incident(request: IncidentAnalysisRequest):
        return await services.analyze_incident(request.model_dump())
else:
    app = None
