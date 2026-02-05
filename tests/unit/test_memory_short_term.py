"""Unit tests for short-term memory."""

import asyncio
from datetime import datetime

from genxai.core.memory.base import Memory, MemoryType
from genxai.core.memory.short_term import ShortTermMemory


def test_short_term_store_and_retrieve() -> None:
    memory = ShortTermMemory(capacity=2)
    mem = Memory(id="1", content="hello", type=MemoryType.SHORT_TERM, timestamp=datetime.now())
    memory.store(mem)
    assert memory.retrieve("1") == mem


def test_short_term_eviction() -> None:
    memory = ShortTermMemory(capacity=2)
    memory.store(Memory(id="1", content="a", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    memory.store(Memory(id="2", content="b", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    memory.store(Memory(id="3", content="c", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    assert memory.retrieve("1") is None
    assert memory.retrieve("2") is not None
    assert memory.retrieve("3") is not None


def test_short_term_search() -> None:
    memory = ShortTermMemory(capacity=3)
    memory.store(Memory(id="1", content="alpha", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    memory.store(Memory(id="2", content="beta", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    memory.store(Memory(id="3", content="alphonse", type=MemoryType.SHORT_TERM, timestamp=datetime.now()))
    matches = memory.search("alp")
    assert len(matches) == 2


def test_short_term_context_async() -> None:
    memory = ShortTermMemory(capacity=2)

    async def run() -> None:
        await memory.add({"message": "Hello"})
        await memory.add({"message": "World"})
        context = await memory.get_context()
        assert "Hello" in context
        assert "World" in context

    asyncio.run(run())
