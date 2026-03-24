"""Async inference queue with Redis/RQ support and in-memory fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

LOGGER = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except Exception:
    redis = None
    REDIS_AVAILABLE = False

try:
    from rq import Queue
    RQ_AVAILABLE = True
except Exception:
    Queue = None
    RQ_AVAILABLE = False


class InferenceQueue:
    """Queue abstraction for async detector jobs and batch inference."""

    def __init__(self) -> None:
        self.queue_name = os.environ.get("TRUSTSPHERE_QUEUE", "trustsphere_inference")
        self.redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        self._memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._redis_client = redis.from_url(self.redis_url) if REDIS_AVAILABLE else None
        self._rq_queue = Queue(self.queue_name, connection=self._redis_client.sync_client()) if REDIS_AVAILABLE and RQ_AVAILABLE and self._redis_client is not None else None

    async def enqueue(self, task: dict[str, Any]) -> None:
        if self._redis_client is not None:
            await self._redis_client.rpush(self.queue_name, json.dumps(task))
        else:
            await self._memory_queue.put(task)

    async def enqueue_batch(self, tasks: list[dict[str, Any]]) -> None:
        for task in tasks:
            await self.enqueue(task)

    async def dequeue(self) -> dict[str, Any]:
        if self._redis_client is not None:
            result = await self._redis_client.blpop(self.queue_name, timeout=1)
            if result is None:
                return {}
            _, payload = result
            return json.loads(payload)
        try:
            return await asyncio.wait_for(self._memory_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return {}
