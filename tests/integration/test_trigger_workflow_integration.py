"""Integration test for trigger-driven workflow execution."""

import asyncio
import hmac
import hashlib
import pytest
from pathlib import Path
import sys
import tempfile

from genxai_enterprise.triggers.file_watcher import FileWatcherTrigger
from genxai_enterprise.triggers.queue import QueueTrigger
from genxai_enterprise.triggers.registry import TriggerRegistry
from genxai_enterprise.triggers.schedule import ScheduleTrigger
from genxai_enterprise.triggers.webhook import WebhookTrigger
from genxai.core.graph.trigger_runner import TriggerWorkflowRunner
from genxai.llm.factory import LLMProviderFactory

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from tests.utils.mock_llm import MockLLMProvider  # noqa: E402


@pytest.fixture(autouse=True)
def mock_llm_provider(monkeypatch):
    def _create_provider(*args, **kwargs):
        model = kwargs.get("model") or (args[0] if args else "mock-model")
        return MockLLMProvider(model=model)

    monkeypatch.setattr(LLMProviderFactory, "create_provider", _create_provider)


@pytest.mark.asyncio
async def test_webhook_trigger_executes_workflow():
    nodes = [
        {"id": "start", "type": "input"},
        {
            "id": "agent_1",
            "type": "agent",
            "config": {"role": "Test", "goal": "Handle trigger"},
        },
        {"id": "end", "type": "output"},
    ]
    edges = [
        {"source": "start", "target": "agent_1"},
        {"source": "agent_1", "target": "end"},
    ]

    runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)
    secret = "super-secret"
    trigger = WebhookTrigger(trigger_id="integration_webhook", secret=secret)

    results = []

    async def on_event(event):
        result = await runner.handle_event(event)
        results.append(result)

    trigger.on_event(on_event)
    await trigger.start()

    payload = {"task": "hello"}
    raw_body = b"{\"task\": \"hello\"}"
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    response = await trigger.handle_request(
        payload=payload,
        raw_body=raw_body,
        headers={"X-GenXAI-Signature": signature},
    )
    await asyncio.sleep(0.1)

    await trigger.stop()

    assert response["status"] == "accepted"
    assert len(results) == 1
    assert results[0]["status"] in {"success", "error"}

    rejected = await trigger.handle_request(
        payload=payload,
        raw_body=raw_body,
        headers={"X-GenXAI-Signature": "sha256=bad"},
    )
    assert rejected["status"] == "rejected"


@pytest.mark.asyncio
async def test_queue_trigger_executes_workflow():
    nodes = [
        {"id": "start", "type": "input"},
        {
            "id": "agent_1",
            "type": "agent",
            "config": {"role": "Test", "goal": "Handle queue"},
        },
        {"id": "end", "type": "output"},
    ]
    edges = [
        {"source": "start", "target": "agent_1"},
        {"source": "agent_1", "target": "end"},
    ]

    runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)
    trigger = QueueTrigger(trigger_id="integration_queue")

    results = []
    done = asyncio.Event()

    async def on_event(event):
        result = await runner.handle_event(event)
        results.append(result)
        done.set()

    trigger.on_event(on_event)
    await trigger.start()

    await trigger.enqueue({"task": "queue hello"})
    await asyncio.wait_for(done.wait(), timeout=3.0)

    await trigger.stop()

    assert len(results) == 1
    assert results[0]["status"] in {"success", "error"}


@pytest.mark.asyncio
async def test_schedule_trigger_executes_workflow():
    pytest.importorskip("apscheduler")

    nodes = [
        {"id": "start", "type": "input"},
        {
            "id": "agent_1",
            "type": "agent",
            "config": {"role": "Test", "goal": "Handle schedule"},
        },
        {"id": "end", "type": "output"},
    ]
    edges = [
        {"source": "start", "target": "agent_1"},
        {"source": "agent_1", "target": "end"},
    ]

    runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)
    trigger = ScheduleTrigger(trigger_id="integration_schedule", interval_seconds=1)

    results = []

    async def on_event(event):
        result = await runner.handle_event(event)
        results.append(result)

    trigger.on_event(on_event)
    await trigger.start()
    await asyncio.sleep(1.2)
    await trigger.stop()

    assert len(results) >= 1
    assert results[0]["status"] in {"success", "error"}


@pytest.mark.asyncio
async def test_queue_trigger_custom_queue_injection():
    custom_queue = asyncio.Queue()
    trigger = QueueTrigger(trigger_id="custom_queue", queue=custom_queue)
    events = []

    async def on_event(event):
        events.append(event.payload)

    trigger.on_event(on_event)
    await trigger.start()
    await custom_queue.put({"task": "custom"})
    for _ in range(10):
        if events:
            break
        await asyncio.sleep(0.1)
    await trigger.stop()

    assert events == [{"task": "custom"}]


@pytest.mark.asyncio
async def test_queue_trigger_non_dict_payload():
    trigger = QueueTrigger(trigger_id="non_dict_payload")
    events = []

    async def on_event(event):
        events.append(event.payload)

    trigger.on_event(on_event)
    await trigger.start()
    await trigger.enqueue({"task": "will_be_dict"})
    await trigger.queue.put("hello")
    for _ in range(10):
        if len(events) >= 2:
            break
        await asyncio.sleep(0.1)
    await trigger.stop()

    assert {"task": "will_be_dict"} in events
    assert {"message": "hello"} in events


@pytest.mark.asyncio
async def test_trigger_registry_start_stop_all():
    TriggerRegistry.clear()

    trigger_a = QueueTrigger(trigger_id="registry_a")
    trigger_b = QueueTrigger(trigger_id="registry_b")

    TriggerRegistry.register(trigger_a)
    TriggerRegistry.register(trigger_b)

    await TriggerRegistry.start_all()
    stats = TriggerRegistry.get_stats()
    assert stats.get("running") == 2

    await TriggerRegistry.stop_all()
    stats = TriggerRegistry.get_stats()
    assert stats.get("stopped") == 2

    await TriggerRegistry.stop_all()
    stats = TriggerRegistry.get_stats()
    assert stats.get("stopped") == 2

    await TriggerRegistry.start_all()
    stats = TriggerRegistry.get_stats()
    assert stats.get("running") == 2

    TriggerRegistry.clear()


def test_trigger_registry_unhandled_unregister_and_empty_stats():
    TriggerRegistry.clear()
    TriggerRegistry.unregister("missing")
    stats = TriggerRegistry.get_stats()
    assert stats["total"] == 0


@pytest.mark.asyncio
async def test_file_watcher_trigger_emits_event():
    pytest.importorskip("watchdog")

    events = []
    done = asyncio.Event()

    async def on_event(event):
        events.append(event.payload)
        done.set()

    with tempfile.TemporaryDirectory() as tmpdir:
        watch_path = Path(tmpdir)
        trigger = FileWatcherTrigger(trigger_id="watch_files", watch_path=watch_path)
        trigger.on_event(on_event)
        await trigger.start()

        done.clear()
        new_dir = watch_path / "subdir"
        new_dir.mkdir()
        await asyncio.wait_for(done.wait(), timeout=5.0)

        target = watch_path / "sample.txt"
        target.write_text("hello")
        await asyncio.wait_for(done.wait(), timeout=5.0)

        done.clear()
        target.write_text("hello again")
        await asyncio.wait_for(done.wait(), timeout=5.0)

        done.clear()
        moved = watch_path / "sample-moved.txt"
        target.rename(moved)
        await asyncio.wait_for(done.wait(), timeout=5.0)

        done.clear()
        moved.unlink()
        await asyncio.wait_for(done.wait(), timeout=5.0)
        await trigger.stop()

    assert events
    event_types = {payload.get("event_type") for payload in events}
    assert "created" in event_types
    assert "modified" in event_types
    assert any("dest_path" in payload for payload in events)
    assert "deleted" in event_types
    target_path = str(target)
    moved_path = str(moved)
    new_dir_path = str(new_dir)
    assert any(payload.get("src_path") == target_path for payload in events)
    assert any(
        payload.get("src_path") == new_dir_path and payload.get("is_directory")
        for payload in events
    )
    assert any(
        payload.get("dest_path") == moved_path
        or payload.get("src_path") == moved_path
        for payload in events
    )
    assert any(
        payload.get("event_type") == "deleted"
        and payload.get("src_path") == moved_path
        for payload in events
    )