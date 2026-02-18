"""Tests for memory system."""

import pytest
from pathlib import Path
from genxai.core.memory.manager import MemorySystem
from genxai.core.memory.base import Memory, MemoryType, MemoryConfig
from genxai.core.memory.long_term import LongTermMemory
from genxai.core.memory.persistence import MemoryPersistenceConfig


class _FakeRecord:
    def __init__(self, payload_key: str, payload: dict):
        self._payload_key = payload_key
        self._payload = payload

    def get(self, key: str):
        if key == self._payload_key:
            return self._payload
        return None


class _FakeGraphSession:
    def __init__(self, storage: dict):
        self.storage = storage

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query: str, **params):
        query = query.strip()

        if "MERGE (e:Episode" in query:
            self.storage["episodes"][params["id"]] = {
                "id": params["id"],
                "agent_id": params["agent_id"],
                "task": params["task"],
                "actions_json": params["actions_json"],
                "outcome_json": params["outcome_json"],
                "timestamp": params["timestamp"],
                "duration": params["duration"],
                "success": params["success"],
                "metadata_json": params["metadata_json"],
            }
            return []

        if "MATCH (e:Episode {id: $episode_id})" in query:
            episode = self.storage["episodes"].get(params["episode_id"])
            return [_FakeRecord("e", episode)] if episode else []

        if "MATCH (e:Episode {agent_id: $agent_id})" in query:
            episodes = [
                ep
                for ep in self.storage["episodes"].values()
                if ep["agent_id"] == params["agent_id"]
                and (not params["success_only"] or ep["success"])
            ]
            episodes.sort(key=lambda ep: ep["timestamp"], reverse=True)
            return [_FakeRecord("e", ep) for ep in episodes[: params["limit"]]]

        if "MATCH (e:Episode)" in query and "CONTAINS" in query:
            keywords = params["keywords"]
            episodes = [
                ep
                for ep in self.storage["episodes"].values()
                if any(word in ep["task"].lower() for word in keywords)
            ]
            episodes.sort(key=lambda ep: (ep["success"], ep["timestamp"]), reverse=True)
            return [_FakeRecord("e", ep) for ep in episodes[: params["limit"]]]

        if "MERGE (f:Fact" in query:
            self.storage["facts"][params["id"]] = {
                "id": params["id"],
                "subject": params["subject"],
                "predicate": params["predicate"],
                "object": params["object"],
                "confidence": params["confidence"],
                "source": params["source"],
                "timestamp": params["timestamp"],
                "metadata_json": params["metadata_json"],
            }
            return []

        if "MATCH (f:Fact {subject: $subject})" in query:
            facts = [
                f
                for f in self.storage["facts"].values()
                if f["subject"] == params["subject"]
                and (params["predicate"] is None or f["predicate"] == params["predicate"])
            ]
            return [_FakeRecord("f", f) for f in facts]

        if "MATCH (f:Fact {predicate: $predicate})" in query:
            facts = [
                f
                for f in self.storage["facts"].values()
                if f["predicate"] == params["predicate"]
                and (params["subject"] is None or f["subject"] == params["subject"])
                and (params["object"] is None or f["object"] == params["object"])
            ]
            return [_FakeRecord("f", f) for f in facts]

        if "MATCH (f:Fact {object: $object})" in query:
            facts = [
                f
                for f in self.storage["facts"].values()
                if f["object"] == params["object"]
                and (params["predicate"] is None or f["predicate"] == params["predicate"])
            ]
            return [_FakeRecord("f", f) for f in facts]

        return []


class _FakeGraphDriver:
    def __init__(self):
        self.storage = {"episodes": {}, "facts": {}}

    def session(self):
        return _FakeGraphSession(self.storage)


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
    assert "backend_plugins" in stats


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

    stats = await reloaded.get_stats()
    assert "sqlite" in stats.get("backend_plugins", {})


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
async def test_graph_backed_episodic_persistence_queries():
    graph_driver = _FakeGraphDriver()
    memory = MemorySystem(agent_id="agent_graph", graph_db=graph_driver)

    episode = await memory.store_episode(
        task="deploy service",
        actions=[{"type": "cmd", "value": "pytest -q"}],
        outcome={"status": "ok"},
        duration=2.5,
        success=True,
    )

    assert episode is not None
    fetched = await memory.episodic.retrieve_episode(episode.id)  # type: ignore[union-attr]
    assert fetched is not None
    assert fetched.task == "deploy service"

    by_agent = await memory.episodic.retrieve_by_agent("agent_graph", limit=10, success_only=True)  # type: ignore[union-attr]
    assert len(by_agent) >= 1

    similar = await memory.episodic.retrieve_similar_tasks("deploy", limit=5)  # type: ignore[union-attr]
    assert len(similar) >= 1

    stats = await memory.get_stats()
    episodic_stats = stats.get("episodic", {})
    assert "backend_telemetry" in episodic_stats
    assert episodic_stats["backend_telemetry"]["backend"] == "neo4j"


@pytest.mark.asyncio
async def test_graph_backed_semantic_persistence_queries():
    graph_driver = _FakeGraphDriver()
    memory = MemorySystem(agent_id="agent_graph", graph_db=graph_driver)

    fact = await memory.store_fact("service", "status", "healthy", confidence=0.9, source="monitor")
    assert fact is not None

    by_subject = await memory.semantic.retrieve_by_subject("service")  # type: ignore[union-attr]
    assert len(by_subject) == 1
    assert by_subject[0].object == "healthy"

    by_predicate = await memory.semantic.retrieve_by_predicate("status", subject="service")  # type: ignore[union-attr]
    assert len(by_predicate) == 1

    by_object = await memory.semantic.retrieve_by_object("healthy")  # type: ignore[union-attr]
    assert len(by_object) == 1

    stats = await memory.get_stats()
    semantic_stats = stats.get("semantic", {})
    assert "backend_telemetry" in semantic_stats
    assert semantic_stats["backend_telemetry"]["backend"] == "neo4j"


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
