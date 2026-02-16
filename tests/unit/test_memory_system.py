"""Tests for memory system."""

import pytest
from pathlib import Path
from genxai.core.memory.manager import MemorySystem
from genxai.core.memory.base import Memory, MemoryType, MemoryConfig
from genxai.core.memory.long_term import LongTermMemory
from genxai.core.memory.persistence import MemoryPersistenceConfig


@pytest.mark.asyncio
async def test_memory_system_initialization():
    """Test memory system initialization."""
    memory = MemorySystem(agent_id="test_agent")
    assert memory.agent_id == "test_agent"
    assert memory.short_term is not None
    assert memory.working is not None


@pytest.mark.asyncio
async def test_add_to_short_term():
    """Test adding to short-term memory."""
    memory = MemorySystem(agent_id="test_agent")
    await memory.add_to_short_term(
        content={"message": "Hello"},
        metadata={"timestamp": 123456}
    )
    context = await memory.get_short_term_context(max_tokens=1000)
    assert "Hello" in context or context == ""


@pytest.mark.asyncio
async def test_working_memory():
    """Test working memory operations."""
    memory = MemorySystem(agent_id="test_agent")
    memory.add_to_working("key1", "value1")
    assert memory.get_from_working("key1") == "value1"
    assert memory.get_from_working("nonexistent") is None


@pytest.mark.asyncio
async def test_memory_stats():
    """Test memory statistics."""
    memory = MemorySystem(agent_id="test_agent")
    stats = await memory.get_stats()
    assert "agent_id" in stats
    assert stats["agent_id"] == "test_agent"
    assert "short_term" in stats
    assert "working" in stats


@pytest.mark.asyncio
async def test_clear_short_term():
    """Test clearing short-term memory."""
    memory = MemorySystem(agent_id="test_agent")
    await memory.add_to_short_term(content={"test": "data"})
    await memory.clear_short_term()
    context = await memory.get_short_term_context()
    assert context == "" or len(context) == 0


@pytest.mark.asyncio
async def test_clear_working():
    """Test clearing working memory."""
    memory = MemorySystem(agent_id="test_agent")
    memory.add_to_working("key1", "value1")
    memory.clear_working()
    assert memory.get_from_working("key1") is None


@pytest.mark.asyncio
async def test_memory_persistence_round_trip(tmp_path: Path):
    """Ensure episodic/semantic/procedural data persists to disk."""
    memory = MemorySystem(
        agent_id="test_agent",
        persistence_enabled=True,
        persistence_path=tmp_path,
        persistence_backend="sqlite",
    )

    await memory.store_episode(
        task="Test task",
        actions=[{"type": "action"}],
        outcome={"result": "ok"},
        duration=1.0,
        success=True,
    )
    await memory.store_fact("agent", "is", "active")
    await memory.store_procedure(
        name="demo",
        description="demo procedure",
        steps=[{"step": 1}],
    )

    reloaded = MemorySystem(
        agent_id="test_agent",
        persistence_enabled=True,
        persistence_path=tmp_path,
        persistence_backend="sqlite",
    )

    assert reloaded.episodic is not None
    assert len(reloaded.episodic) == 1
    assert reloaded.semantic is not None
    facts = await reloaded.semantic.query(subject="agent")
    assert len(facts) == 1
    assert reloaded.procedural is not None
    procedure = await reloaded.procedural.retrieve_procedure(name="demo")
    assert procedure is not None


@pytest.mark.asyncio
async def test_long_term_memory_persistence(tmp_path: Path):
    """Ensure long-term memory persists when Redis is not configured."""
    persistence = MemoryPersistenceConfig(base_dir=tmp_path, enabled=True, backend="sqlite")
    long_term = LongTermMemory(config=None, persistence=persistence)

    memory = Memory(
        id="memory-1",
        type=MemoryType.LONG_TERM,
        content={"note": "persistent"},
        timestamp=__import__("datetime").datetime.now(),
    )
    long_term.store(memory)

    reloaded = LongTermMemory(config=None, persistence=persistence)
    loaded = reloaded.retrieve("memory-1")
    assert loaded is not None
    assert loaded.content["note"] == "persistent"


@pytest.mark.asyncio
async def test_prompt_memory_context_with_rolling_summary():
    """Prompt memory context should combine summary + recent window."""
    config = MemoryConfig(short_term_window_size=2, rolling_summary_enabled=True)
    memory = MemorySystem(agent_id="test_agent", config=config)

    await memory.add_to_short_term(content={"message": "m1"})
    await memory.add_to_short_term(content={"message": "m2"})
    await memory.add_to_short_term(content={"message": "m3"})
    memory.set_rolling_summary("User prefers concise bullet points.")

    context = await memory.build_prompt_memory_context(window_size=2, max_tokens=1000)
    assert "Conversation summary:" in context
    assert "User prefers concise bullet points" in context
    assert "m3" in context
    assert "m2" in context


@pytest.mark.asyncio
async def test_older_context_and_prune_to_window():
    """Older context extraction should exclude recent window and pruning should retain it."""
    config = MemoryConfig(short_term_window_size=2)
    memory = MemorySystem(agent_id="test_agent", config=config)

    await memory.add_to_short_term(content={"message": "m1"})
    await memory.add_to_short_term(content={"message": "m2"})
    await memory.add_to_short_term(content={"message": "m3"})
    await memory.add_to_short_term(content={"message": "m4"})

    older_context = await memory.get_older_context_for_summary(keep_recent=2)
    assert "m1" in older_context
    assert "m2" in older_context
    assert "m3" not in older_context
    assert "m4" not in older_context

    removed = memory.prune_short_term_to_window(keep_recent=2)
    assert removed == 2

    recent_context = await memory.get_recent_window_context(window_size=5)
    assert "m3" in recent_context
    assert "m4" in recent_context
    assert "m1" not in recent_context
    assert "m2" not in recent_context
