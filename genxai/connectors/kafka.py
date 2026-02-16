"""Kafka connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional, Callable
import asyncio
import json
import logging

from .base import Connector

logger = logging.getLogger(__name__)


class KafkaConnector(Connector):
    """Kafka connector using aiokafka."""

    def __init__(
        self,
        connector_id: str,
        topic: str,
        bootstrap_servers: str,
        group_id: Optional[str] = None,
        name: Optional[str] = None,
        value_deserializer: Optional[Callable[[bytes], Any]] = None,
        poll_interval: float = 0.1,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.value_deserializer = value_deserializer or self._default_deserializer
        self.poll_interval = poll_interval
        self._consumer: Any = None
        self._task: Optional[asyncio.Task[None]] = None

    async def _start(self) -> None:
        from aiokafka import AIOKafkaConsumer

        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=True,
            value_deserializer=self.value_deserializer,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def _stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

    async def validate_config(self) -> None:
        if not self.topic:
            raise ValueError("Kafka topic must be provided")
        if not self.bootstrap_servers:
            raise ValueError("Kafka bootstrap_servers must be provided")

    async def _consume_loop(self) -> None:
        while True:
            try:
                msg = await self._consumer.getone()
                payload = msg.value
                await self.emit(
                    payload=payload,
                    metadata={
                        "topic": msg.topic,
                        "partition": msg.partition,
                        "offset": msg.offset,
                        "timestamp": msg.timestamp,
                    },
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Kafka consumer error: %s", exc)
                await asyncio.sleep(self.poll_interval)

    def _default_deserializer(self, raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return raw

    async def handle_message(self, payload: Dict[str, Any]) -> None:
        await self.emit(payload=payload)