"""Queue-based trigger implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging

from genxai.triggers.base import BaseTrigger

logger = logging.getLogger(__name__)


class QueueTrigger(BaseTrigger):
    """Async queue trigger.

    This trigger listens to an asyncio.Queue instance. It can be swapped
    for custom queue backends by feeding messages into the queue.
    """

    def __init__(
        self,
        trigger_id: str,
        queue: Optional[asyncio.Queue] = None,
        name: Optional[str] = None,
        poll_interval: float = 0.1,
    ) -> None:
        super().__init__(trigger_id=trigger_id, name=name)
        self.queue = queue or asyncio.Queue()
        self.poll_interval = poll_interval
        self._task: Optional[asyncio.Task] = None

    async def _start(self) -> None:
        self._task = asyncio.create_task(self._listen())
        logger.info("QueueTrigger %s started", self.trigger_id)

    async def _stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("QueueTrigger %s stopped", self.trigger_id)

    async def _listen(self) -> None:
        while True:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=self.poll_interval)
                payload: Dict[str, Any]
                if isinstance(message, dict):
                    payload = message
                else:
                    payload = {"message": message}
                await self.emit(payload=payload)
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("QueueTrigger %s error: %s", self.trigger_id, exc)
                await asyncio.sleep(self.poll_interval)

    async def enqueue(self, payload: Dict[str, Any]) -> None:
        """Helper to push payloads into the trigger queue."""
        await self.queue.put(payload)