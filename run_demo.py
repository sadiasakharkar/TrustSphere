from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
API_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("TRUSTSPHERE_API_KEY", "trustsphere-local-dev-key")


def _request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(f"{API_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_api(timeout_seconds: int = 30) -> dict:
    started = time.time()
    while time.time() - started < timeout_seconds:
        try:
            return _request("/system/health")
        except URLError:
            time.sleep(1)
    raise RuntimeError("TrustSphere API did not become ready in time")


def main() -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "security_ai.api.app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        try:
            health = wait_for_api()
            pipeline = _request("/system/test-pipeline", method="POST")
            incidents = _request("/incidents")
        except Exception:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            from fastapi.testclient import TestClient
            from security_ai.api.app import app

            with TestClient(app) as client:
                health = client.get("/system/health", headers={"x-api-key": API_KEY}).json()
                pipeline = client.post("/system/test-pipeline", headers={"x-api-key": API_KEY}).json()
                incidents = client.get("/incidents", headers={"x-api-key": API_KEY}).json()
        print("TrustSphere Demo Ready")
        print(json.dumps({
            "health": health.get("data", {}),
            "pipeline_test": pipeline.get("data", {}),
            "incident_count": len(incidents.get("data", [])),
        }, indent=2))
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
