"""Kafka consumer scaffold for streaming TrustSphere events."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from security_ai.api.queue import InferenceQueue

LOGGER = logging.getLogger(__name__)

try:
    from aiokafka import AIOKafkaConsumer
    KAFKA_AVAILABLE = True
except Exception:
    AIOKafkaConsumer = None
    KAFKA_AVAILABLE = False


async def consume_events() -> None:
    if not KAFKA_AVAILABLE:
        LOGGER.warning("aiokafka not installed; Kafka consumer is inactive.")
        return
    broker = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.environ.get("KAFKA_TOPIC", "trustsphere-events")
    queue = InferenceQueue()
    consumer = AIOKafkaConsumer(topic, bootstrap_servers=broker, value_deserializer=lambda value: json.loads(value.decode("utf-8")))
    await consumer.start()
    try:
        async for message in consumer:
            await queue.enqueue(message.value)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    asyncio.run(consume_events())
