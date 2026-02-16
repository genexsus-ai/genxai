"""AWS SQS connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import json
import logging


from .base import Connector

logger = logging.getLogger(__name__)


class SQSConnector(Connector):
    """SQS connector using aioboto3."""

    def __init__(
        self,
        connector_id: str,
        queue_url: str,
        region: Optional[str] = None,
        name: Optional[str] = None,
        poll_interval: float = 1.0,
        wait_time_seconds: int = 10,
        max_messages: int = 10,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.queue_url = queue_url
        self.region = region
        self.poll_interval = poll_interval
        self.wait_time_seconds = wait_time_seconds
        self.max_messages = max_messages
        self._task: Optional[asyncio.Task[None]] = None
        self._session = None

    async def _start(self) -> None:
        self._task = asyncio.create_task(self._poll_loop())

    async def _stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def validate_config(self) -> None:
        if not self.queue_url:
            raise ValueError("SQS queue_url must be provided")

    async def _poll_loop(self) -> None:
        while True:
            try:
                if self._session is None:
                    import aioboto3

                    self._session = aioboto3.Session()
                async with self._session.client("sqs", region_name=self.region) as client:
                    response = await client.receive_message(
                        QueueUrl=self.queue_url,
                        MaxNumberOfMessages=self.max_messages,
                        WaitTimeSeconds=self.wait_time_seconds,
                    )
                    messages = response.get("Messages", [])
                    for message in messages:
                        body = message.get("Body")
                        payload = self._deserialize(body)
                        await self.emit(
                            payload=payload,
                            metadata={
                                "message_id": message.get("MessageId"),
                                "receipt_handle": message.get("ReceiptHandle"),
                            },
                        )
                        await client.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message.get("ReceiptHandle"),
                        )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("SQS poll error: %s", exc)
                await asyncio.sleep(self.poll_interval)

    def _deserialize(self, body: Optional[str]) -> Any:
        if body is None:
            return None
        try:
            return json.loads(body)
        except Exception:
            return body

    async def handle_message(self, payload: Dict[str, Any]) -> None:
        await self.emit(payload=payload)