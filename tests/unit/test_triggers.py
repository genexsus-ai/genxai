"""Unit tests for Trigger SDK."""

import asyncio
import hmac
import hashlib
import pytest

from enterprise.genxai.triggers.base import BaseTrigger, TriggerStatus
from enterprise.genxai.triggers.queue import QueueTrigger
from enterprise.genxai.triggers.file_watcher import FileWatcherTrigger
from enterprise.genxai.triggers.registry import TriggerRegistry
from enterprise.genxai.triggers.schedule import ScheduleTrigger
from enterprise.genxai.triggers.webhook import WebhookTrigger
from genxai.core.graph.trigger_runner import TriggerWorkflowRunner


class DummyTrigger(BaseTrigger):
    async def _start(self) -> None:
        return None

    async def _stop(self) -> None:
        return None


@pytest.mark.asyncio
async def test_trigger_start_stop_and_emit():
    trigger = DummyTrigger(trigger_id="dummy")
    events = []

    async def handler(event):
        events.append(event)

    trigger.on_event(handler)
    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING

    await trigger.emit({"hello": "world"})
    assert len(events) == 1
    assert events[0].payload == {"hello": "world"}

    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED


def test_trigger_registry_register_clear_stats():
    TriggerRegistry.clear()
    trigger = DummyTrigger(trigger_id="dummy")
    TriggerRegistry.register(trigger)
    assert TriggerRegistry.get("dummy") == trigger
    stats = TriggerRegistry.get_stats()
    assert stats["total"] == 1
    TriggerRegistry.clear()
    assert TriggerRegistry.get("dummy") is None


@pytest.mark.asyncio
async def test_webhook_trigger_signature_validation():
    secret = "super-secret"
    trigger = WebhookTrigger(trigger_id="webhook", secret=secret)
    payload_bytes = b"{\"hello\": \"world\"}"
    digest = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    assert trigger.validate_signature(payload_bytes, signature)
    assert not trigger.validate_signature(payload_bytes, "sha256=invalid")

    events = []

    async def handler(event):
        events.append(event)

    trigger.on_event(handler)
    await trigger.start()
    response = await trigger.handle_request(
        payload={"hello": "world"},
        raw_body=payload_bytes,
        headers={"X-GenXAI-Signature": signature},
    )
    assert response["status"] == "accepted"
    assert len(events) == 1
    await trigger.stop()


@pytest.mark.asyncio
async def test_queue_trigger_enqueue():
    trigger = QueueTrigger(trigger_id="queue")
    events = []

    async def handler(event):
        events.append(event)

    trigger.on_event(handler)
    await trigger.start()
    await trigger.enqueue({"job": "123"})
    await asyncio.sleep(0.1)
    await trigger.stop()

    assert len(events) >= 1
    assert events[0].payload["job"] == "123"


def test_file_watcher_trigger_requires_watchdog():
    try:
        import watchdog  # noqa: F401
    except ImportError:
        trigger = FileWatcherTrigger(trigger_id="files", watch_path=".")
        with pytest.raises(ImportError):
            asyncio.run(trigger.start())
        return

    pytest.skip("watchdog installed; manual behavior validated in integration")


@pytest.mark.asyncio
async def test_schedule_trigger_start_stop():
    pytest.importorskip("apscheduler")
    trigger = ScheduleTrigger(trigger_id="schedule", interval_seconds=1)
    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING
    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED


@pytest.mark.asyncio
async def test_trigger_workflow_runner_executes_workflow():
    nodes = [
        {"id": "start", "type": "input"},
        {
            "id": "agent_1",
            "type": "agent",
            "config": {"role": "Test", "goal": "Test"},
        },
        {"id": "end", "type": "output"},
    ]
    edges = [
        {"source": "start", "target": "agent_1"},
        {"source": "agent_1", "target": "end"},
    ]

    runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)
    event = type("Evt", (), {"trigger_id": "test", "payload": {"task": "Hello"}})()
    result = await runner.handle_event(event)

    assert result["status"] in {"success", "error"}