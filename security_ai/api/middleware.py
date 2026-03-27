"""Enterprise security middleware and helpers for the TrustSphere API."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
import json
import logging
import os
from threading import Lock
import time
from typing import Any
from uuid import uuid4
from security_ai.api.core.response import ResponseFactory

try:
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
except Exception:
    HTTPException = Exception
    Request = object
    JSONResponse = object

LOGGER = logging.getLogger(__name__)

API_KEY_HEADER = "x-api-key"
REQUEST_ID_HEADER = "x-request-id"
DEFAULT_API_KEY = os.getenv("TRUSTSPHERE_API_KEY", "trustsphere-local-dev-key")
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("TRUSTSPHERE_RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("TRUSTSPHERE_RATE_LIMIT_MAX_REQUESTS", "120"))
MAX_REQUEST_SIZE_BYTES = int(os.getenv("TRUSTSPHERE_MAX_REQUEST_SIZE_BYTES", str(1024 * 1024)))
AUTH_EXEMPT_PATHS = {"/health", "/system/health", "/auth/login", "/auth/signup", "/auth/me", "/auth/refresh"}


class InMemoryRateLimiter:
    """Simple per-client sliding-window rate limiter for offline deployments."""

    def __init__(self, max_requests: int = RATE_LIMIT_MAX_REQUESTS, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client_id: str) -> tuple[bool, int, int]:
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._events[client_id]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return False, len(bucket), retry_after
            bucket.append(now)
            return True, len(bucket), 0


class APIKeyAuthenticator:
    """Offline API key validator using a local environment-backed secret."""

    def __init__(self, expected_key: str = DEFAULT_API_KEY, header_name: str = API_KEY_HEADER) -> None:
        self.expected_key = expected_key
        self.header_name = header_name

    def validate(self, request: Request) -> None:
        if getattr(request, "url", None) is None or request.url.path in AUTH_EXEMPT_PATHS:
            return
        provided_key = request.headers.get(self.header_name)
        if not provided_key or provided_key != self.expected_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key.")


rate_limiter = InMemoryRateLimiter()
authenticator = APIKeyAuthenticator()


def build_success_payload(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return ResponseFactory.success(
        data=data,
        meta={
            **(meta or {}),
        },
    )


def build_error_payload(
    message: str,
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return ResponseFactory.error(message, data=None, meta=meta or {})


def success_response(data: Any, *, meta: dict[str, Any] | None = None, status_code: int = 200):
    return JSONResponse(status_code=status_code, content=build_success_payload(data=data, meta=meta))


def error_response(status_code: int, message: str, *, meta: dict[str, Any] | None = None):
    return JSONResponse(status_code=200, content=build_error_payload(message=message, meta={"originalStatus": status_code, **(meta or {})}))


def ensure_request_id(request: Request) -> str:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    request.state.request_id = request_id
    return request_id


def client_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if getattr(request, "client", None) and getattr(request.client, "host", None):
        return str(request.client.host)
    return "unknown-client"


def read_json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def structured_log(logger: logging.Logger, event: str, **fields: Any) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logger.info(json.dumps(payload, default=str, sort_keys=True))
