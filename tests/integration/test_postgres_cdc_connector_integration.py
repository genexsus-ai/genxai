"""Integration-style tests for PostgresCDCConnector using mocks."""

import asyncio
import sys
import types
import pytest


@pytest.mark.asyncio
async def test_postgres_cdc_connector_emits_changes(monkeypatch):
    emitted = []
    done = asyncio.Event()

    class FakeConn:
        async def execute(self, *args, **kwargs):
            return None

        async def fetch(self, *args, **kwargs):
            return [{"data": "{\"change\": true}"}]

        async def close(self):
            return None

    async def fake_connect(*args, **kwargs):
        return FakeConn()

    fake_module = types.SimpleNamespace(connect=fake_connect)
    sys.modules["asyncpg"] = fake_module
    from genxai_enterprise.connectors.postgres_cdc import PostgresCDCConnector

    connector = PostgresCDCConnector(
        connector_id="p1",
        dsn="postgres://",
        slot_name="slot",
        publication="pub",
        poll_interval=0,
    )
    async def _on_event(event):
        emitted.append(event.payload)
        done.set()

    connector.on_event(_on_event)

    await connector.start()
    await asyncio.wait_for(done.wait(), timeout=2)
    await connector.stop()

    assert emitted and emitted[0] == {"change": True}