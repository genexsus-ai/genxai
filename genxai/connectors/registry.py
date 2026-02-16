"""Connector registry for GenXAI integrations."""

from __future__ import annotations

from typing import Dict, List, Optional
import logging

from .base import Connector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Registry for connectors."""

    _connectors: Dict[str, Connector] = {}

    @classmethod
    def register(cls, connector: Connector) -> None:
        if connector.connector_id in cls._connectors:
            logger.warning("Connector %s already registered", connector.connector_id)
        cls._connectors[connector.connector_id] = connector

    @classmethod
    def unregister(cls, connector_id: str) -> None:
        cls._connectors.pop(connector_id, None)

    @classmethod
    def get(cls, connector_id: str) -> Optional[Connector]:
        return cls._connectors.get(connector_id)

    @classmethod
    def list_all(cls) -> List[Connector]:
        return list(cls._connectors.values())

    @classmethod
    async def start_all(cls) -> None:
        for connector in cls._connectors.values():
            await connector.start()

    @classmethod
    async def stop_all(cls) -> None:
        for connector in cls._connectors.values():
            await connector.stop()