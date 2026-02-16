"""Memory system manager coordinating all memory types."""

from typing import Any, Dict, List, Optional, Tuple
import logging
import asyncio
from datetime import datetime

from pathlib import Path
from genxai.core.memory.base import Memory, MemoryType, MemoryConfig
from genxai.core.memory.short_term import ShortTermMemory
from genxai.core.memory.long_term import LongTermMemory
from genxai.core.memory.episodic import EpisodicMemory, Episode
from genxai.core.memory.semantic import SemanticMemory, Fact
from genxai.core.memory.procedural import ProceduralMemory, Procedure
from genxai.core.memory.working import WorkingMemory
from genxai.core.memory.vector_store import VectorStoreFactory
from genxai.core.memory.embedding import EmbeddingServiceFactory
from genxai.core.memory.persistence import MemoryPersistenceConfig
from genxai.utils.tokens import truncate_to_token_limit

logger = logging.getLogger(__name__)


class MemorySystem:
    """Comprehensive memory management system.
    
    Orchestrates all memory types:
    - Short-term: Recent interactions
    - Long-term: Persistent memories with vector search
    - Episodic: Agent experiences and episodes
    - Semantic: Facts and knowledge
    - Procedural: Learned skills and procedures
    - Working: Active processing context
    """

    def __init__(
        self,
        agent_id: str,
        config: Optional[MemoryConfig] = None,
        vector_store_backend: Optional[str] = None,
        embedding_provider: Optional[str] = None,
        persistence_enabled: bool = False,
        persistence_path: Optional[Path] = None,
        persistence_backend: str = "json",
        persistence_sqlite_path: Optional[Path] = None,
    ) -> None:
        """Initialize memory system.

        Args:
            agent_id: ID of the agent this memory belongs to
            config: Memory configuration
            vector_store_backend: Vector store backend ("chromadb", "pinecone")
            embedding_provider: Embedding provider ("openai", "local", "cohere")
        """
        self.agent_id = agent_id
        self.config = config or MemoryConfig()
        self._persistence = MemoryPersistenceConfig(
            base_dir=persistence_path or Path(".genxai/memory"),
            enabled=persistence_enabled,
            backend=persistence_backend,
            sqlite_path=persistence_sqlite_path,
        )

        # Rolling-summary state for prompt-memory compression
        self.rolling_summary: str = ""
        self.summary_updated_at: Optional[datetime] = None
        self.summary_version: int = 0

        # Initialize short-term memory
        self.short_term = ShortTermMemory(capacity=self.config.short_term_capacity)

        # Initialize working memory
        self.working = WorkingMemory(capacity=self.config.working_capacity)

        # Initialize long-term memory with vector store
        self.long_term: Optional[LongTermMemory] = None
        self.vector_store = None
        self.embedding_service = None
        
        if self.config.long_term_enabled:
            try:
                # Create vector store
                backend = vector_store_backend or self.config.vector_db
                if backend:
                    self.vector_store = VectorStoreFactory.create(
                        backend=backend,
                    )
                
                # Create embedding service
                provider = embedding_provider or "openai"
                if provider:
                    self.embedding_service = EmbeddingServiceFactory.create(
                        provider=provider,
                    )
                
                # Initialize long-term memory
                self.long_term = LongTermMemory(
                    config=self.config,
                    vector_store=self.vector_store,
                    embedding_service=self.embedding_service,
                    persistence=self._persistence,
                )
                logger.info("Long-term memory initialized with vector store")
            except Exception as e:
                logger.warning(f"Failed to initialize long-term memory: {e}")
                self.long_term = LongTermMemory(
                    config=self.config,
                    persistence=self._persistence,
                )

        # Initialize episodic memory
        self.episodic: Optional[EpisodicMemory] = None
        if self.config.episodic_enabled:
            self.episodic = EpisodicMemory(persistence=self._persistence)
            logger.info("Episodic memory initialized")

        # Initialize semantic memory
        self.semantic: Optional[SemanticMemory] = None
        if self.config.semantic_enabled:
            self.semantic = SemanticMemory(persistence=self._persistence)
            logger.info("Semantic memory initialized")

        # Initialize procedural memory
        self.procedural: Optional[ProceduralMemory] = None
        if self.config.procedural_enabled:
            self.procedural = ProceduralMemory(persistence=self._persistence)
            logger.info("Procedural memory initialized")

        logger.info(f"Memory system initialized for agent: {agent_id}")

    # ==================== Short-term Memory ====================

    async def add_to_short_term(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add content to short-term memory.

        Args:
            content: Content to store
            metadata: Optional metadata
        """
        await self.short_term.add(content, metadata)

    async def get_short_term_context(self, max_tokens: int = 4000) -> str:
        """Get context from short-term memory for LLM.

        Args:
            max_tokens: Maximum tokens to include

        Returns:
            Formatted context string
        """
        return await self.short_term.get_context(max_tokens)

    async def get_recent_window_context(self, window_size: Optional[int] = None) -> str:
        """Get context from the most recent short-term memories.

        Args:
            window_size: Number of recent memories to include

        Returns:
            Formatted recent-memory context string
        """
        size = window_size or self.config.short_term_window_size
        recent_memories = self.short_term.retrieve_recent(limit=size)
        return self.short_term.format_memories_as_context(
            recent_memories,
            header="Recent turns:",
        )

    async def get_older_context_for_summary(self, keep_recent: Optional[int] = None) -> str:
        """Get older short-term memories to be summarized.

        Args:
            keep_recent: Number of recent entries to exclude from summary input

        Returns:
            Formatted older-memory context string
        """
        window = keep_recent or self.config.short_term_window_size
        older_memories = self.short_term.retrieve_older_than_recent(window)
        return self.short_term.format_memories_as_context(
            older_memories,
            header="Older turns:",
        )

    def prune_short_term_to_window(self, keep_recent: Optional[int] = None) -> int:
        """Prune short-term memory to keep only the latest N entries.

        Args:
            keep_recent: Number of recent entries to retain

        Returns:
            Number of removed entries
        """
        window = keep_recent or self.config.short_term_window_size
        return self.short_term.prune_to_recent(window)

    def set_rolling_summary(self, summary: str) -> None:
        """Set rolling summary text with configured token bound."""
        bounded = truncate_to_token_limit(
            summary or "",
            self.config.rolling_summary_max_tokens,
            preserve_start=False,
        )
        self.rolling_summary = bounded
        self.summary_updated_at = datetime.now()
        self.summary_version += 1

    def get_rolling_summary(self) -> str:
        """Get current rolling summary text."""
        return self.rolling_summary

    async def build_prompt_memory_context(
        self,
        window_size: Optional[int] = None,
        max_tokens: int = 2000,
    ) -> str:
        """Build prompt-ready memory context from summary + recent turns.

        Args:
            window_size: Sliding-window size for recent turns
            max_tokens: Token budget for final memory context

        Returns:
            Formatted and token-bounded memory context
        """
        parts: List[str] = []

        if self.config.rolling_summary_enabled and self.rolling_summary:
            parts.append(f"Conversation summary:\n{self.rolling_summary}")

        recent_context = await self.get_recent_window_context(window_size=window_size)
        if recent_context:
            parts.append(recent_context)

        context = "\n\n".join(parts)
        if not context:
            return ""
        return truncate_to_token_limit(context, max_tokens=max_tokens, preserve_start=False)

    async def clear_short_term(self) -> None:
        """Clear short-term memory."""
        # clear() is sync; clear_async() is the async variant.
        await self.short_term.clear_async()

    # ==================== Working Memory ====================

    def add_to_working(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add item to working memory.

        Args:
            key: Item key
            value: Item value
            metadata: Optional metadata
        """
        self.working.add(key, value, metadata)

    def get_from_working(self, key: str) -> Optional[Any]:
        """Get item from working memory.

        Args:
            key: Item key

        Returns:
            Item value if found
        """
        return self.working.get(key)

    def clear_working(self) -> None:
        """Clear working memory."""
        self.working.clear()

    # ==================== Long-term Memory ====================

    async def add_to_long_term(
        self,
        memory: Memory,
        ttl: Optional[int] = None,
    ) -> None:
        """Add memory to long-term storage.

        Args:
            memory: Memory to store
            ttl: Time-to-live in seconds
        """
        if self.long_term is None:
            logger.warning("Long-term memory not enabled")
            return

        # Generate embedding if vector store available
        if self.embedding_service and self.vector_store:
            try:
                embedding = await self.embedding_service.embed(str(memory.content))
                await self.vector_store.store(memory, embedding)
                logger.debug(f"Stored memory in vector store: {memory.id}")
            except Exception as e:
                logger.error(f"Failed to store in vector store: {e}")

        # Store in long-term memory
        self.long_term.store(memory, ttl)

    async def search_long_term(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Tuple[Memory, float]]:
        """Search long-term memory by semantic similarity.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (memory, similarity_score) tuples
        """
        if self.vector_store is None or self.embedding_service is None:
            logger.warning("Vector search not available")
            return []

        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)
            
            # Search vector store
            results = await self.vector_store.search(query_embedding, limit=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to search long-term memory: {e}")
            return []

    # ==================== Episodic Memory ====================

    async def store_episode(
        self,
        task: str,
        actions: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        duration: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Episode]:
        """Store an episode.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Outcome
            duration: Duration in seconds
            success: Success flag
            metadata: Optional metadata

        Returns:
            Created episode
        """
        if self.episodic is None:
            logger.warning("Episodic memory not enabled")
            return None

        return await self.episodic.store_episode(
            agent_id=self.agent_id,
            task=task,
            actions=actions,
            outcome=outcome,
            duration=duration,
            success=success,
            metadata=metadata,
        )

    async def get_similar_episodes(
        self,
        task: str,
        limit: int = 5,
    ) -> List[Episode]:
        """Get episodes similar to a task.

        Args:
            task: Task description
            limit: Maximum results

        Returns:
            List of similar episodes
        """
        if self.episodic is None:
            return []

        return await self.episodic.retrieve_similar_tasks(task, limit)

    async def get_success_rate(
        self,
        task_pattern: Optional[str] = None,
    ) -> float:
        """Get success rate for tasks.

        Args:
            task_pattern: Optional task pattern filter

        Returns:
            Success rate (0.0 to 1.0)
        """
        if self.episodic is None:
            return 0.0

        return await self.episodic.get_success_rate(
            agent_id=self.agent_id,
            task_pattern=task_pattern,
        )

    # ==================== Semantic Memory ====================

    async def store_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: Optional[str] = None,
    ) -> Optional[Fact]:
        """Store a fact.

        Args:
            subject: Subject entity
            predicate: Relationship/property
            object: Object entity/value
            confidence: Confidence score
            source: Source of fact

        Returns:
            Created fact
        """
        if self.semantic is None:
            logger.warning("Semantic memory not enabled")
            return None

        return await self.semantic.store_fact(
            subject=subject,
            predicate=predicate,
            object=object,
            confidence=confidence,
            source=source,
        )

    async def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Fact]:
        """Query facts.

        Args:
            subject: Optional subject filter
            predicate: Optional predicate filter
            object: Optional object filter

        Returns:
            List of matching facts
        """
        if self.semantic is None:
            return []

        return await self.semantic.query(
            subject=subject,
            predicate=predicate,
            object=object,
        )

    # ==================== Procedural Memory ====================

    async def store_procedure(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
    ) -> Optional[Procedure]:
        """Store a procedure.

        Args:
            name: Procedure name
            description: Description
            steps: List of steps
            preconditions: Required preconditions
            postconditions: Expected postconditions

        Returns:
            Created procedure
        """
        if self.procedural is None:
            logger.warning("Procedural memory not enabled")
            return None

        return await self.procedural.store_procedure(
            name=name,
            description=description,
            steps=steps,
            preconditions=preconditions,
            postconditions=postconditions,
        )

    async def get_procedure(self, name: str) -> Optional[Procedure]:
        """Get a procedure by name.

        Args:
            name: Procedure name

        Returns:
            Procedure if found
        """
        if self.procedural is None:
            return None

        return await self.procedural.retrieve_procedure(name=name)

    async def record_procedure_execution(
        self,
        procedure_id: str,
        success: bool,
        duration: float,
    ) -> bool:
        """Record procedure execution.

        Args:
            procedure_id: Procedure ID
            success: Success flag
            duration: Duration in seconds

        Returns:
            True if recorded
        """
        if self.procedural is None:
            return False

        return await self.procedural.record_execution(
            procedure_id=procedure_id,
            success=success,
            duration=duration,
        )

    # ==================== Memory Consolidation ====================

    async def consolidate_memories(
        self,
        importance_threshold: float = 0.7,
    ) -> Dict[str, int]:
        """Consolidate important memories from short-term to long-term.

        Args:
            importance_threshold: Minimum importance to consolidate

        Returns:
            Statistics about consolidation
        """
        if self.long_term is None:
            logger.warning("Long-term memory not enabled")
            return {"consolidated": 0}

        consolidated = 0
        
        # Get important memories from short-term
        for memory in self.short_term.memories:
            if memory.importance >= importance_threshold:
                # Move to long-term
                await self.add_to_long_term(memory)
                consolidated += 1

        logger.info(f"Consolidated {consolidated} memories to long-term")
        
        return {
            "consolidated": consolidated,
            "threshold": importance_threshold,
        }

    # ==================== Statistics ====================

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "agent_id": self.agent_id,
            "short_term": self.short_term.get_stats(),
            "working": self.working.get_stats(),
        }

        if self.long_term:
            stats["long_term"] = self.long_term.get_stats()

        if self.episodic:
            stats["episodic"] = await self.episodic.get_stats()

        if self.semantic:
            stats["semantic"] = await self.semantic.get_stats()

        if self.procedural:
            stats["procedural"] = await self.procedural.get_stats()

        if self.vector_store:
            try:
                stats["vector_store"] = await self.vector_store.get_stats()
            except Exception as exc:
                logger.warning("Vector store stats unavailable: %s", exc)
                stats["vector_store"] = {"error": str(exc)}

        stats["persistence"] = {
            "enabled": self._persistence.enabled,
            "path": str(self._persistence.base_dir),
        }

        stats["rolling_summary"] = {
            "enabled": self.config.rolling_summary_enabled,
            "version": self.summary_version,
            "updated_at": self.summary_updated_at.isoformat() if self.summary_updated_at else None,
            "token_budget": self.config.rolling_summary_max_tokens,
            "has_summary": bool(self.rolling_summary),
        }

        return stats

    def __repr__(self) -> str:
        """String representation."""
        enabled = []
        if self.short_term:
            enabled.append("short_term")
        if self.working:
            enabled.append("working")
        if self.long_term:
            enabled.append("long_term")
        if self.episodic:
            enabled.append("episodic")
        if self.semantic:
            enabled.append("semantic")
        if self.procedural:
            enabled.append("procedural")
        
        return f"MemorySystem(agent_id={self.agent_id}, enabled={enabled})"

    async def aclose(self) -> None:
        """Close underlying vector store/embedding service if supported."""
        if self.embedding_service and hasattr(self.embedding_service, "aclose"):
            try:
                await self.embedding_service.aclose()
            except Exception as exc:
                logger.warning("Failed to close embedding service: %s", exc)

        if self.vector_store and hasattr(self.vector_store, "aclose"):
            try:
                await self.vector_store.aclose()
            except Exception as exc:
                logger.warning("Failed to close vector store: %s", exc)

    def close(self) -> None:
        """Synchronously close resources where possible."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.aclose())
            return

        if loop.is_closed():
            return
        loop.create_task(self.aclose())
