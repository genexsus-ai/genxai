"""Unit tests for shared memory bus."""

import pytest

from genxai.core.memory.shared import SharedMemoryBus


@pytest.mark.asyncio
async def test_shared_memory_bus_set_get():
    bus = SharedMemoryBus()
    await bus.set("key", "value")
    assert bus.get("key") == "value"


@pytest.mark.asyncio
async def test_shared_memory_bus_subscribe():
    bus = SharedMemoryBus()
    updates = []

    async def on_update(entry):
        updates.append(entry.value)

    bus.subscribe("plan", on_update)
    await bus.set("plan", 1)
    assert updates == [1]