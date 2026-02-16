"""Base trigger abstractions for GenXAI workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class TriggerStatus(str, Enum):
    """Lifecycle status for triggers."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class TriggerEvent:
    """Event emitted by triggers to start workflows."""

    trigger_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTrigger(ABC):
    """Abstract base class for workflow triggers."""

    def __init__(self, trigger_id: str, name: Optional[str] = None) -> None:
        self.trigger_id = trigger_id
        self.name = name or trigger_id
        self.status: TriggerStatus = TriggerStatus.STOPPED
        self._callbacks: list[Callable[[TriggerEvent], Awaitable[None]]] = []
        self._lock = asyncio.Lock()

    def on_event(self, callback: Callable[[TriggerEvent], Awaitable[None]]) -> None:
        """Register a callback to receive trigger events."""
        self._callbacks.append(callback)

    async def emit(self, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Emit a trigger event to registered callbacks."""
        event = TriggerEvent(
            trigger_id=self.trigger_id,
            payload=payload,
            metadata=metadata or {},
        )
        if not self._callbacks:
            logger.warning("Trigger %s emitted event with no subscribers", self.trigger_id)
            return

        await asyncio.gather(*[callback(event) for callback in self._callbacks])

    async def start(self) -> None:
        """Start the trigger."""
        async with self._lock:
            if self.status in {TriggerStatus.RUNNING, TriggerStatus.STARTING}:
                return
            self.status = TriggerStatus.STARTING
            try:
                await self._start()
                self.status = TriggerStatus.RUNNING
                logger.info("Trigger started: %s", self.trigger_id)
            except Exception as exc:
                self.status = TriggerStatus.ERROR
                logger.error("Failed to start trigger %s: %s", self.trigger_id, exc)
                raise

    async def stop(self) -> None:
        """Stop the trigger."""
        async with self._lock:
            if self.status in {TriggerStatus.STOPPED, TriggerStatus.STOPPING}:
                return
            self.status = TriggerStatus.STOPPING
            try:
                await self._stop()
                self.status = TriggerStatus.STOPPED
                logger.info("Trigger stopped: %s", self.trigger_id)
            except Exception as exc:
                self.status = TriggerStatus.ERROR
                logger.error("Failed to stop trigger %s: %s", self.trigger_id, exc)
                raise

    @abstractmethod
    async def _start(self) -> None:
        """Implement trigger-specific start logic."""
        raise NotImplementedError

    @abstractmethod
    async def _stop(self) -> None:
        """Implement trigger-specific stop logic."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.trigger_id}, status={self.status})"