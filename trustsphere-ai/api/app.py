"""FastAPI entry point for TrustSphere AI."""

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline.inference_pipeline import run_inference

app = FastAPI(title="TrustSphere AI API")


class InferenceRequest(BaseModel):
    record: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "trustsphere-ai", "offline_mode": True}


@app.post("/inference")
def inference(payload: InferenceRequest) -> dict:
    return run_inference(payload.record)
