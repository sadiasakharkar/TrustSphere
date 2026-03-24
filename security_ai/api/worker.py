"""Background async inference worker."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from security_ai.api.queue import InferenceQueue
from security_ai.api.services import DetectorService

LOGGER = logging.getLogger(__name__)


async def run_worker() -> None:
    queue = InferenceQueue()
    services = DetectorService()
    handlers = {
        "email": services.detect_email,
        "url": services.detect_url,
        "credential": services.detect_credential,
        "attachment": services.detect_attachment,
        "incident": services.analyze_incident,
    }
    while True:
        task = await queue.dequeue()
        if not task:
            await asyncio.sleep(0.1)
            continue
        task_type = task.get("type")
        payload = task.get("payload", {})
        handler = handlers.get(task_type)
        if handler is None:
            LOGGER.warning("Unknown task type: %s", task_type)
            continue
        result = await handler(payload)
        LOGGER.info("Processed %s task: %s", task_type, result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    asyncio.run(run_worker())
