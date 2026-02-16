"""Integration-style tests for SQSConnector using mocks."""

import asyncio
import sys
import pytest


@pytest.mark.asyncio
async def test_sqs_connector_emits_messages(monkeypatch):
    emitted = []
    done = asyncio.Event()

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def receive_message(self, **kwargs):
            return {"Messages": [{"Body": "{\"ok\": true}", "MessageId": "1", "ReceiptHandle": "r1"}]}

        async def delete_message(self, **kwargs):
            return None

    class FakeSession:
        def client(self, *args, **kwargs):
            return FakeClient()

    class FakeBoto:
        def Session(self):
            return FakeSession()

    sys.modules["aioboto3"] = FakeBoto()
    from genxai_enterprise.connectors.sqs import SQSConnector

    connector = SQSConnector(connector_id="s1", queue_url="url", poll_interval=0)
    async def _on_event(event):
        emitted.append(event.payload)
        done.set()

    connector.on_event(_on_event)

    await connector.start()
    await asyncio.wait_for(done.wait(), timeout=2)
    await connector.stop()

    assert emitted and emitted[0] == {"ok": True}