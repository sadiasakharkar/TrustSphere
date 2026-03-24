"""Unified FastAPI service for the TrustSphere Security AI platform."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

try:
    from fastapi import FastAPI, HTTPException, Response
except Exception:
    FastAPI = None
    HTTPException = Exception
    Response = object

from security_ai.api.metrics import FALSE_POSITIVE_GAUGE, MODEL_DRIFT_GAUGE, REQUEST_COUNTER, REQUEST_LATENCY, metrics_payload
from security_ai.api.model_registry import ModelRegistry
from security_ai.api.services import DetectorService


class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: str
    attachments: str = ""


class URLRequest(BaseModel):
    url: str


class CredentialRequest(BaseModel):
    text: str
    commit_message: str = ""
    paste_context: str = ""


class AttachmentRequest(BaseModel):
    filename: str
    size_bytes: int
    content_text: str = ""
    event_context: str = ""
    post_download_action: str = ""


class IncidentRequest(BaseModel):
    summary: str = ""
    severity: str = "LOW"
    indicators: list[str] = []
    evidence: list[str] = []


if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI Platform", version="1.0.0")
    services = DetectorService()
    registry = ModelRegistry(base_dir=__import__("pathlib").Path(__file__).resolve().parents[1])

    @app.on_event("startup")
    async def startup_event() -> None:
        registry.register_model("email", {"endpoint": "/detect/email"})
        registry.register_model("url", {"endpoint": "/detect/url"})
        registry.register_model("credential", {"endpoint": "/detect/credential"})
        registry.register_model("attachment", {"endpoint": "/detect/attachment"})
        registry.register_model("incident", {"endpoint": "/analyze/incident"})
        FALSE_POSITIVE_GAUGE.labels("email").set(0.0)
        MODEL_DRIFT_GAUGE.labels("email").set(0.0)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "service": "security-ai", "async_inference": True}

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_payload()
        return Response(content=payload, media_type=content_type)

    @app.post("/detect/email")
    async def detect_email(request: EmailRequest):
        return await _timed_call("/detect/email", services.detect_email, request.model_dump())

    @app.post("/detect/url")
    async def detect_url(request: URLRequest):
        return await _timed_call("/detect/url", services.detect_url, request.model_dump())

    @app.post("/detect/credential")
    async def detect_credential(request: CredentialRequest):
        return await _timed_call("/detect/credential", services.detect_credential, request.model_dump())

    @app.post("/detect/attachment")
    async def detect_attachment(request: AttachmentRequest):
        return await _timed_call("/detect/attachment", services.detect_attachment, request.model_dump())

    @app.post("/analyze/incident")
    async def analyze_incident(request: IncidentRequest):
        return await _timed_call("/analyze/incident", services.analyze_incident, request.model_dump())


    async def _timed_call(endpoint: str, handler, payload: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            result = await handler(payload)
            REQUEST_COUNTER.labels(endpoint, "success").inc()
            return result
        except Exception as exc:
            REQUEST_COUNTER.labels(endpoint, "error").inc()
            raise HTTPException(status_code=500, detail=str(exc))
        finally:
            REQUEST_LATENCY.labels(endpoint).observe(time.perf_counter() - start)
else:
    app = None
