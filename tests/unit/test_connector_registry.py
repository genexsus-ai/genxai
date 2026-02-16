"""Unit tests for connector registry lifecycle helpers."""

import pytest

from enterprise.genxai.connectors.base import Connector
from enterprise.genxai.connectors.registry import ConnectorRegistry


class DummyConnector(Connector):
    def __init__(self, connector_id: str) -> None:
        super().__init__(connector_id=connector_id)
        self.started = False
        self.stopped = False

    async def _start(self) -> None:
        self.started = True

    async def _stop(self) -> None:
        self.stopped = True


@pytest.mark.asyncio
async def test_connector_registry_start_stop_all():
    connector = DummyConnector("dummy")
    ConnectorRegistry.register(connector)

    await ConnectorRegistry.start_all()
    assert connector.started is True

    await ConnectorRegistry.stop_all()
    assert connector.stopped is True

    ConnectorRegistry.unregister("dummy")