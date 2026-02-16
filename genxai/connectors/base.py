"""Base connector abstractions for GenXAI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectorStatus(str, Enum):
    """Lifecycle status for connectors."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ConnectorEvent:
    """Event emitted by connectors."""

    connector_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


class Connector(ABC):
    """Abstract base class for connector integrations."""

    def __init__(self, connector_id: str, name: Optional[str] = None) -> None:
        self.connector_id = connector_id
        self.name = name or connector_id
        self.status: ConnectorStatus = ConnectorStatus.STOPPED
        self._callbacks: list[Callable[[ConnectorEvent], Awaitable[None]]] = []
        self._lock = asyncio.Lock()
        self._last_error: Optional[str] = None
        self._last_healthcheck: Optional[str] = None

    def on_event(self, callback: Callable[[ConnectorEvent], Awaitable[None]]) -> None:
        """Register a callback to receive connector events."""
        self._callbacks.append(callback)

    async def emit(self, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Emit connector event to subscribers."""
        event = ConnectorEvent(
            connector_id=self.connector_id,
            payload=payload,
            metadata=metadata or {},
        )
        if not self._callbacks:
            logger.warning("Connector %s emitted event with no subscribers", self.connector_id)
            return

        await asyncio.gather(*[callback(event) for callback in self._callbacks])

    async def start(self) -> None:
        """Start the connector."""
        async with self._lock:
            if self.status in {ConnectorStatus.RUNNING, ConnectorStatus.STARTING}:
                return
            self.status = ConnectorStatus.STARTING
            try:
                await self.validate_config()
                await self._start()
                self.status = ConnectorStatus.RUNNING
                self._last_error = None
                logger.info("Connector started: %s", self.connector_id)
            except Exception as exc:
                self.status = ConnectorStatus.ERROR
                self._last_error = str(exc)
                logger.error("Failed to start connector %s: %s", self.connector_id, exc)
                raise

    async def stop(self) -> None:
        """Stop the connector."""
        async with self._lock:
            if self.status in {ConnectorStatus.STOPPED, ConnectorStatus.STOPPING}:
                return
            self.status = ConnectorStatus.STOPPING
            try:
                await self._stop()
                self.status = ConnectorStatus.STOPPED
                self._last_error = None
                logger.info("Connector stopped: %s", self.connector_id)
            except Exception as exc:
                self.status = ConnectorStatus.ERROR
                self._last_error = str(exc)
                logger.error("Failed to stop connector %s: %s", self.connector_id, exc)
                raise

    async def health_check(self) -> Dict[str, Any]:
        """Return a health payload for the connector."""
        status = "ok" if self.status == ConnectorStatus.RUNNING else "not_running"
        payload = {
            "connector_id": self.connector_id,
            "status": status,
            "lifecycle": self.status.value,
            "last_error": self._last_error,
        }
        self._last_healthcheck = datetime.now(UTC).isoformat()
        return payload

    async def validate_config(self) -> None:
        """Validate connector configuration before start."""
        return None

    @abstractmethod
    async def _start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _stop(self) -> None:
        raise NotImplementedError