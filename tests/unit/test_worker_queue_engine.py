"""Unit tests for the worker queue engine."""

import asyncio
import pytest

from genxai.core.execution import WorkerQueueEngine


@pytest.mark.asyncio
async def test_worker_queue_engine_processes_payloads():
    engine = WorkerQueueEngine(worker_count=1)
    processed = []

    async def handler(payload: dict) -> None:
        processed.append(payload["value"])

    await engine.start()
    await engine.enqueue({"value": 1}, handler)
    await engine.enqueue({"value": 2}, handler)

    for _ in range(20):
        if processed == [1, 2]:
            break
        await asyncio.sleep(0.05)

    await engine.stop()

    assert processed == [1, 2]


@pytest.mark.asyncio
async def test_worker_queue_engine_retries():
    engine = WorkerQueueEngine(worker_count=1, max_retries=2, backoff_seconds=0)
    attempts = {"count": 0}

    async def handler(payload: dict) -> None:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("fail once")

    await engine.start()
    await engine.enqueue({"value": 1}, handler)

    for _ in range(20):
        if attempts["count"] >= 2:
            break
        await asyncio.sleep(0.05)

    await engine.stop()

    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_worker_queue_engine_uses_registered_handler():
    engine = WorkerQueueEngine(worker_count=1)
    processed = []

    async def handler(payload: dict) -> None:
        processed.append(payload["value"])

    engine.register_handler("test", handler)

    await engine.start()
    await engine.enqueue({"value": 42}, handler_name="test")

    for _ in range(20):
        if processed == [42]:
            break
        await asyncio.sleep(0.05)

    await engine.stop()

    assert processed == [42]