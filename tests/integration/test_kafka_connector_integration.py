"""Integration-style tests for KafkaConnector using mocks."""

import asyncio
import types
import sys

import pytest


@pytest.mark.asyncio
async def test_kafka_connector_emits_messages(monkeypatch):
    messages = []

    class FakeMessage:
        topic = "topic"
        partition = 0
        offset = 1
        timestamp = 123

        def __init__(self, value):
            self.value = value

    class FakeConsumer:
        def __init__(self, *args, **kwargs):
            self._value = {"hello": "world"}

        async def start(self):
            return None

        async def stop(self):
            return None

        async def getone(self):
            await asyncio.sleep(0)
            return FakeMessage(self._value)

    fake_module = types.SimpleNamespace(AIOKafkaConsumer=FakeConsumer)
    sys.modules["aiokafka"] = fake_module
    from genxai_enterprise.connectors.kafka import KafkaConnector

    connector = KafkaConnector(connector_id="k1", topic="topic", bootstrap_servers="localhost:9092")
    connector.on_event(lambda event: messages.append(event.payload))

    await connector.start()
    await asyncio.sleep(0.05)
    await connector.stop()

    assert messages == [{"hello": "world"}]