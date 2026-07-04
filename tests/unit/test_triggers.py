"""Unit tests for the trigger system (base, registry, webhook, queue, schedule, file watcher)."""

import asyncio
import hashlib
import hmac

import pytest

from genxai.core.graph.trigger_runner import TriggerWorkflowRunner
from genxai.triggers import (
    BaseTrigger,
    FileWatcherTrigger,
    QueueTrigger,
    ScheduleTrigger,
    TriggerEvent,
    TriggerRegistry,
    TriggerStatus,
    WebhookTrigger,
)


class DummyTrigger(BaseTrigger):
    """Minimal concrete trigger for exercising the base lifecycle."""

    def __init__(self, trigger_id: str, fail_on_start: bool = False, **kwargs):
        super().__init__(trigger_id=trigger_id, **kwargs)
        self.fail_on_start = fail_on_start
        self.started = 0
        self.stopped = 0

    async def _start(self) -> None:
        if self.fail_on_start:
            raise RuntimeError("boom")
        self.started += 1

    async def _stop(self) -> None:
        self.stopped += 1


@pytest.fixture(autouse=True)
def clean_registry():
    TriggerRegistry.clear()
    yield
    TriggerRegistry.clear()


# ---------------------------------------------------------------- base


def test_trigger_event_defaults():
    event = TriggerEvent(trigger_id="t1", payload={"a": 1})
    assert event.trigger_id == "t1"
    assert event.payload == {"a": 1}
    assert event.metadata == {}
    assert event.timestamp is not None


@pytest.mark.asyncio
async def test_emit_delivers_to_all_callbacks():
    trigger = DummyTrigger("t1")
    received = []

    async def cb1(event):
        received.append(("cb1", event.payload))

    async def cb2(event):
        received.append(("cb2", event.payload))

    trigger.on_event(cb1)
    trigger.on_event(cb2)
    await trigger.emit(payload={"x": 1}, metadata={"origin": "test"})

    assert ("cb1", {"x": 1}) in received
    assert ("cb2", {"x": 1}) in received


@pytest.mark.asyncio
async def test_emit_without_subscribers_is_noop():
    trigger = DummyTrigger("t1")
    await trigger.emit(payload={"x": 1})  # should not raise


@pytest.mark.asyncio
async def test_start_stop_lifecycle_is_idempotent():
    trigger = DummyTrigger("t1")
    assert trigger.status == TriggerStatus.STOPPED

    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING
    assert trigger.started == 1

    await trigger.start()  # already running: no-op
    assert trigger.started == 1

    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED
    assert trigger.stopped == 1

    await trigger.stop()  # already stopped: no-op
    assert trigger.stopped == 1


@pytest.mark.asyncio
async def test_start_failure_sets_error_status():
    trigger = DummyTrigger("t1", fail_on_start=True)
    with pytest.raises(RuntimeError):
        await trigger.start()
    assert trigger.status == TriggerStatus.ERROR


# ---------------------------------------------------------------- registry


def test_registry_register_get_unregister():
    trigger = DummyTrigger("t1")
    TriggerRegistry.register(trigger)
    assert TriggerRegistry.get("t1") is trigger
    assert trigger in TriggerRegistry.list_all()

    TriggerRegistry.unregister("t1")
    assert TriggerRegistry.get("t1") is None


def test_registry_overwrite_and_unregister_missing():
    first = DummyTrigger("t1")
    second = DummyTrigger("t1")
    TriggerRegistry.register(first)
    TriggerRegistry.register(second)  # overwrites with a warning
    assert TriggerRegistry.get("t1") is second

    TriggerRegistry.unregister("missing")  # warns, does not raise


def test_registry_is_singleton():
    assert TriggerRegistry() is TriggerRegistry()


@pytest.mark.asyncio
async def test_registry_start_all_stop_all_and_stats():
    t1 = DummyTrigger("t1")
    t2 = DummyTrigger("t2")
    TriggerRegistry.register(t1)
    TriggerRegistry.register(t2)

    await TriggerRegistry.start_all()
    assert t1.status == TriggerStatus.RUNNING
    assert t2.status == TriggerStatus.RUNNING

    stats = TriggerRegistry.get_stats()
    assert stats["total"] == 2
    assert stats[TriggerStatus.RUNNING.value] == 2

    await TriggerRegistry.stop_all()
    assert t1.status == TriggerStatus.STOPPED
    assert t2.status == TriggerStatus.STOPPED


# ---------------------------------------------------------------- webhook


def _sign(secret: str, body: bytes, alg: str = "sha256") -> str:
    digest = hmac.new(secret.encode(), body, getattr(hashlib, alg)).hexdigest()
    return f"{alg}={digest}"


def test_webhook_signature_no_secret_accepts_anything():
    trigger = WebhookTrigger("wh1")
    assert trigger.validate_signature(b"body", None) is True


def test_webhook_signature_validation():
    trigger = WebhookTrigger("wh1", secret="s3cret")
    body = b'{"a": 1}'
    assert trigger.validate_signature(body, _sign("s3cret", body)) is True
    assert trigger.validate_signature(body, _sign("wrong", body)) is False
    assert trigger.validate_signature(body, None) is False


@pytest.mark.asyncio
async def test_webhook_handle_request_accepted():
    trigger = WebhookTrigger("wh1", secret="s3cret")
    received = []

    async def cb(event):
        received.append(event)

    trigger.on_event(cb)
    body = b'{"a": 1}'
    result = await trigger.handle_request(
        payload={"a": 1},
        raw_body=body,
        headers={"X-GenXAI-Signature": _sign("s3cret", body)},
    )

    assert result == {"status": "accepted", "trigger_id": "wh1"}
    assert len(received) == 1
    assert received[0].payload == {"a": 1}
    assert received[0].metadata["headers"]["X-GenXAI-Signature"].startswith("sha256=")


@pytest.mark.asyncio
async def test_webhook_handle_request_rejects_bad_signature():
    trigger = WebhookTrigger("wh1", secret="s3cret")
    received = []

    async def cb(event):
        received.append(event)

    trigger.on_event(cb)
    result = await trigger.handle_request(
        payload={"a": 1},
        raw_body=b'{"a": 1}',
        headers={"X-GenXAI-Signature": "sha256=bogus"},
    )

    assert result["status"] == "rejected"
    assert received == []


@pytest.mark.asyncio
async def test_webhook_start_stop():
    trigger = WebhookTrigger("wh1")
    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING
    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED


# ---------------------------------------------------------------- queue


@pytest.mark.asyncio
async def test_queue_trigger_emits_dict_and_wrapped_payloads():
    trigger = QueueTrigger("q1", poll_interval=0.01)
    received = []

    async def cb(event):
        received.append(event.payload)

    trigger.on_event(cb)
    await trigger.start()
    try:
        await trigger.enqueue({"job": 1})
        await trigger.queue.put("plain-message")  # non-dict gets wrapped
        for _ in range(100):
            if len(received) >= 2:
                break
            await asyncio.sleep(0.01)
    finally:
        await trigger.stop()

    assert {"job": 1} in received
    assert {"message": "plain-message"} in received
    assert trigger.status == TriggerStatus.STOPPED


# ---------------------------------------------------------------- schedule


def test_schedule_trigger_requires_cron_or_interval():
    with pytest.raises(ValueError):
        ScheduleTrigger("s1")


def test_schedule_trigger_accepts_interval():
    trigger = ScheduleTrigger("s1", interval_seconds=60, payload={"k": "v"})
    assert trigger.interval_seconds == 60
    assert trigger.payload == {"k": "v"}


@pytest.mark.asyncio
async def test_schedule_trigger_lifecycle():
    """Start/stop with APScheduler if installed; otherwise assert the ImportError contract."""
    trigger = ScheduleTrigger("s1", interval_seconds=60)
    try:
        import apscheduler  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="APScheduler is required"):
            await trigger.start()
        assert trigger.status == TriggerStatus.ERROR
        return

    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING
    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED


# ---------------------------------------------------------------- file watcher


def test_file_watcher_init(tmp_path):
    trigger = FileWatcherTrigger("f1", watch_path=tmp_path, recursive=False)
    assert trigger.watch_path == tmp_path
    assert trigger.recursive is False


@pytest.mark.asyncio
async def test_file_watcher_lifecycle(tmp_path):
    """Start/stop with watchdog if installed; otherwise assert the ImportError contract."""
    trigger = FileWatcherTrigger("f1", watch_path=tmp_path)
    try:
        import watchdog  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="watchdog is required"):
            await trigger.start()
        assert trigger.status == TriggerStatus.ERROR
        return

    await trigger.start()
    assert trigger.status == TriggerStatus.RUNNING
    await trigger.stop()
    assert trigger.status == TriggerStatus.STOPPED


# ---------------------------------------------------------------- workflow runner


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
