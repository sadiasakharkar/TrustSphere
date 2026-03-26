from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Any = None
    meta: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] | None = None


class ResponseFactory:
    @staticmethod
    def success(data: Any = None, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = APIResponse(success=True, data=data, meta=meta or {}, errors=None)
        return payload.model_dump(mode="json")

    @staticmethod
    def error(message: str, *, data: Any = None, meta: dict[str, Any] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
        payload = APIResponse(success=False, data=data, meta=meta or {}, errors=errors or [message])
        return payload.model_dump(mode="json")
