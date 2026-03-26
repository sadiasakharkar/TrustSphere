from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

class IncidentStreamBroker:
    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: Any) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        message = json.dumps(event, default=str)
        LOGGER.info("[PIPELINE] websocket ✔ event=%s", event.get("type", "unknown"))
        async with self._lock:
            clients = list(self._clients)
        stale = []
        for client in clients:
            try:
                await client.send_text(message)
            except Exception:
                stale.append(client)
        if stale:
            async with self._lock:
                for client in stale:
                    self._clients.discard(client)
