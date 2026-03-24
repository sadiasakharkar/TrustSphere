"""FastAPI-ready phishing email inference API."""

from __future__ import annotations

from pydantic import BaseModel

try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None

from security_ai.predict_email import EmailPredictor


class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: str
    attachments: str = ""


if FastAPI is not None:
    app = FastAPI(title="TrustSphere Security AI")
    predictor = EmailPredictor()

    @app.post("/predict/email")
    def predict_email(request: EmailRequest):
        return predictor.predict(request.subject, request.body, request.sender, request.attachments)
else:
    app = None
