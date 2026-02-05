"""Showcase MemorySystem features across memory types."""

import asyncio
from pathlib import Path

from genxai.core.memory.manager import MemorySystem
from genxai.core.memory.base import Memory, MemoryType


async def main() -> None:
    memory = MemorySystem(
        agent_id="memory_demo",
        persistence_enabled=True,
        persistence_path=Path(".genxai/memory"),
    )

    await memory.add_to_short_term(
        {"task": "remember", "note": "GenXAI remembers context"}
    )
    context = await memory.get_short_term_context()
    print("Short-term context:\n", context)

    long_term_item = Memory(
        content="Persistent insight about agentic workflows",
        memory_type=MemoryType.LONG_TERM,
        importance=0.8,
    )
    await memory.add_to_long_term(long_term_item)

    await memory.store_fact(
        subject="GenXAI",
        predicate="supports",
        object="multi-agent orchestration",
        confidence=0.9,
        source="docs",
    )

    await memory.store_procedure(
        name="run_workflow",
        description="Execute a graph-based workflow",
        steps=[
            {"step": 1, "action": "validate graph"},
            {"step": 2, "action": "execute nodes"},
        ],
    )

    stats = await memory.get_stats()
    print("Memory stats:", stats)


if __name__ == "__main__":
    asyncio.run(main())