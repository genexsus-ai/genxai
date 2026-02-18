"""Long-term memory implementation with Redis backend."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

from genxai.core.memory.base import Memory, MemoryType, MemoryConfig
from genxai.core.memory.persistence import (
    JsonMemoryStore,
    MemoryPersistenceConfig,
    SqliteMemoryStore,
    create_memory_store,
)
from genxai.core.memory.vector_store import VectorStore
from genxai.core.memory.embedding import EmbeddingService
from genxai.core.memory.backends import (
    MemoryBackendPlugin,
    RedisMemoryBackendPlugin,
)

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Long-term memory with persistent Redis storage.
    
    This memory type stores important memories persistently and supports
    TTL-based expiration and importance-based retention.
    """

    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        redis_client: Optional[Any] = None,
        key_prefix: str = "genxai:memory:long_term:",
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        persistence: Optional[MemoryPersistenceConfig] = None,
        backend_plugin: Optional[MemoryBackendPlugin] = None,
    ) -> None:
        """Initialize long-term memory.

        Args:
            config: Memory configuration
            redis_client: Redis client instance (optional, will use in-memory if not provided)
            key_prefix: Prefix for Redis keys
        """
        self.config = config or MemoryConfig()
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._persistence = persistence
        self._backend_plugin = backend_plugin
        if persistence:
            self._store = create_memory_store(persistence)
        else:
            self._store = None
        
        # Fallback to in-memory storage if Redis not available
        self._in_memory_storage: Dict[str, Memory] = {}
        self._use_redis = redis_client is not None
        
        if self._use_redis:
            logger.info("Initialized long-term memory with Redis backend")
            if self._backend_plugin is None:
                self._backend_plugin = RedisMemoryBackendPlugin(
                    redis_client=self._redis,
                    key_prefix=self._key_prefix,
                )
        else:
            logger.warning(
                "Redis client not provided. Using in-memory storage. "
                "Memories will not persist across restarts."
            )

        if self._store and self._persistence and self._persistence.enabled:
            self._load_from_disk()

    def store(
        self,
        memory: Memory,
        ttl: Optional[int] = None,
    ) -> None:
        """Store a memory with optional TTL.

        Args:
            memory: Memory to store
            ttl: Time-to-live in seconds (None for no expiration)
        """
        key = self._make_key(memory.id)
        
        # Serialize memory
        data = self._serialize_memory(memory)
        
        if self._use_redis:
            try:
                # Store in Redis
                if ttl:
                    self._redis.setex(key, ttl, data)
                else:
                    self._redis.set(key, data)
                
                # Store metadata for querying
                self._store_metadata(memory)
                
                logger.debug(f"Stored memory {memory.id} in Redis (TTL: {ttl})")
            except Exception as e:
                logger.error(f"Failed to store memory in Redis: {e}")
                # Fallback to in-memory
                self._in_memory_storage[memory.id] = memory
        else:
            # In-memory storage
            self._in_memory_storage[memory.id] = memory
            logger.debug(f"Stored memory {memory.id} in-memory")

        self._persist()

    def retrieve(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID.

        Args:
            memory_id: ID of memory to retrieve

        Returns:
            Memory if found, None otherwise
        """
        if self._use_redis:
            try:
                key = self._make_key(memory_id)
                data = self._redis.get(key)
                
                if data:
                    memory = self._deserialize_memory(data)
                    
                    # Update access tracking
                    memory.access_count += 1
                    memory.last_accessed = datetime.now()
                    
                    # Update in storage
                    self.store(memory)
                    
                    logger.debug(f"Retrieved memory {memory_id} from Redis")
                    return memory
            except Exception as e:
                logger.error(f"Failed to retrieve memory from Redis: {e}")
        
        # Fallback to in-memory
        if memory_id in self._in_memory_storage:
            memory = self._in_memory_storage[memory_id]
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            logger.debug(f"Retrieved memory {memory_id} from in-memory storage")
            return memory
        
        return None

    def retrieve_by_importance(
        self,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> List[Memory]:
        """Retrieve memories above an importance threshold.

        Args:
            threshold: Minimum importance score
            limit: Maximum number of memories

        Returns:
            List of important memories
        """
        if self._use_redis:
            try:
                # Query metadata index
                pattern = f"{self._key_prefix}*"
                keys = self._redis.keys(pattern)
                
                memories = []
                for key in keys:
                    data = self._redis.get(key)
                    if data:
                        memory = self._deserialize_memory(data)
                        if memory.importance >= threshold:
                            memories.append(memory)
                
                # Sort by importance
                memories.sort(key=lambda m: m.importance, reverse=True)
                
                result = memories[:limit]
                logger.debug(f"Retrieved {len(result)} important memories from Redis")
                return result
            except Exception as e:
                logger.error(f"Failed to query Redis: {e}")
        
        # Fallback to in-memory
        memories = [
            m for m in self._in_memory_storage.values()
            if m.importance >= threshold
        ]
        memories.sort(key=lambda m: m.importance, reverse=True)
        result = memories[:limit]
        logger.debug(f"Retrieved {len(result)} important memories from in-memory storage")
        return result

    def retrieve_recent(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> List[Memory]:
        """Retrieve recent memories within a time window.

        Args:
            days: Number of days to look back
            limit: Maximum number of memories

        Returns:
            List of recent memories
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        if self._use_redis:
            try:
                pattern = f"{self._key_prefix}*"
                keys = self._redis.keys(pattern)
                
                memories = []
                for key in keys:
                    data = self._redis.get(key)
                    if data:
                        memory = self._deserialize_memory(data)
                        if memory.timestamp >= cutoff:
                            memories.append(memory)
                
                # Sort by timestamp (most recent first)
                memories.sort(key=lambda m: m.timestamp, reverse=True)
                
                result = memories[:limit]
                logger.debug(f"Retrieved {len(result)} recent memories from Redis")
                return result
            except Exception as e:
                logger.error(f"Failed to query Redis: {e}")
        
        # Fallback to in-memory
        memories = [
            m for m in self._in_memory_storage.values()
            if m.timestamp >= cutoff
        ]
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        result = memories[:limit]
        logger.debug(f"Retrieved {len(result)} recent memories from in-memory storage")
        return result

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        if self._use_redis:
            try:
                key = self._make_key(memory_id)
                deleted = self._redis.delete(key)
                
                if deleted:
                    self._delete_metadata(memory_id)
                    logger.debug(f"Deleted memory {memory_id} from Redis")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete memory from Redis: {e}")
        
        # Fallback to in-memory
        if memory_id in self._in_memory_storage:
            del self._in_memory_storage[memory_id]
            logger.debug(f"Deleted memory {memory_id} from in-memory storage")
            self._persist()
            return True
        
        return False

    def clear(self) -> None:
        """Clear all memories."""
        if self._use_redis:
            try:
                pattern = f"{self._key_prefix}*"
                keys = self._redis.keys(pattern)
                
                if keys:
                    self._redis.delete(*keys)
                
                logger.info(f"Cleared {len(keys)} memories from Redis")
            except Exception as e:
                logger.error(f"Failed to clear Redis: {e}")
        
        # Clear in-memory storage
        count = len(self._in_memory_storage)
        self._in_memory_storage.clear()
        logger.info(f"Cleared {count} memories from in-memory storage")

        self._persist()

    def get_size(self) -> int:
        """Get current number of stored memories.

        Returns:
            Number of memories
        """
        if self._use_redis:
            try:
                pattern = f"{self._key_prefix}*"
                keys = self._redis.keys(pattern)
                return len(keys)
            except Exception as e:
                logger.error(f"Failed to get size from Redis: {e}")
        
        return len(self._in_memory_storage)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Statistics dictionary
        """
        size = self.get_size()
        
        if size == 0:
            return {
                "size": 0,
                "backend": "redis" if self._use_redis else "in-memory",
                "avg_importance": 0.0,
                "vector_store": bool(self._vector_store),
                "persistence": bool(self._persistence and self._persistence.enabled),
                "backend_telemetry": self._backend_plugin.get_stats() if self._backend_plugin else None,
            }
        
        # Get sample of memories for stats
        if self._use_redis:
            try:
                pattern = f"{self._key_prefix}*"
                keys = list(self._redis.keys(pattern))[:100]  # Sample
                
                memories = []
                for key in keys:
                    data = self._redis.get(key)
                    if data:
                        memories.append(self._deserialize_memory(data))
            except Exception as e:
                logger.error(f"Failed to get stats from Redis: {e}")
                memories = []
        else:
            memories = list(self._in_memory_storage.values())
        
        if not memories:
            return {
                "size": size,
                "backend": "redis" if self._use_redis else "in-memory",
                "avg_importance": 0.0,
                "backend_telemetry": self._backend_plugin.get_stats() if self._backend_plugin else None,
            }
        
        return {
            "size": size,
            "backend": "redis" if self._use_redis else "in-memory",
            "avg_importance": sum(m.importance for m in memories) / len(memories),
            "oldest_memory": min(m.timestamp for m in memories).isoformat(),
            "newest_memory": max(m.timestamp for m in memories).isoformat(),
            "vector_store": bool(self._vector_store),
            "persistence": bool(self._persistence and self._persistence.enabled),
            "backend_telemetry": self._backend_plugin.get_stats() if self._backend_plugin else None,
        }

    async def store_with_embedding(self, memory: Memory, ttl: Optional[int] = None) -> None:
        """Store memory and push embedding to vector store if configured."""
        self.store(memory, ttl)
        if self._vector_store and self._embedding_service:
            try:
                embedding = await self._embedding_service.embed(str(memory.content))
                await self._vector_store.store(memory, embedding)
            except Exception as exc:
                logger.error("Failed to store memory embedding: %s", exc)

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Memory, float]]:
        """Search long-term memory using vector store if available."""
        if not self._vector_store or not self._embedding_service:
            logger.warning("Vector search not available")
            return []

        try:
            query_embedding = await self._embedding_service.embed(query)
            return await self._vector_store.search(query_embedding, limit=limit, filters=filters)
        except Exception as exc:
            logger.error("Failed to search long-term memory: %s", exc)
            return []

    def _persist(self) -> None:
        if not self._store:
            return
        payload = [json.loads(self._serialize_memory(memory)) for memory in self._in_memory_storage.values()]
        self._store.save_list("long_term_memory.json", payload)

    def _load_from_disk(self) -> None:
        if not self._store:
            return
        data = self._store.load_list("long_term_memory.json")
        if not data:
            return
        self._in_memory_storage = {
            item["id"]: self._deserialize_memory(json.dumps(item)) for item in data
        }

    def _make_key(self, memory_id: str) -> str:
        """Create Redis key for memory ID."""
        return f"{self._key_prefix}{memory_id}"

    def _serialize_memory(self, memory: Memory) -> str:
        """Serialize memory to JSON string."""
        data = {
            "id": memory.id,
            "type": memory.type.value,
            "content": memory.content,
            "metadata": memory.metadata,
            "timestamp": memory.timestamp.isoformat(),
            "importance": memory.importance,
            "access_count": memory.access_count,
            "last_accessed": memory.last_accessed.isoformat(),
            "tags": memory.tags,
        }
        return json.dumps(data)

    def _deserialize_memory(self, data: str) -> Memory:
        """Deserialize memory from JSON string."""
        obj = json.loads(data)
        return Memory(
            id=obj["id"],
            type=MemoryType(obj["type"]),
            content=obj["content"],
            metadata=obj["metadata"],
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            importance=obj["importance"],
            access_count=obj["access_count"],
            last_accessed=datetime.fromisoformat(obj["last_accessed"]),
            tags=obj["tags"],
        )

    def _store_metadata(self, memory: Memory) -> None:
        """Store memory metadata for querying (placeholder)."""
        if not self._store:
            return
        if isinstance(self._store, SqliteMemoryStore):
            self._store.store_long_term_metadata(
                memory_id=memory.id,
                memory_type=memory.type.value,
                importance=memory.importance,
                timestamp=memory.timestamp.isoformat(),
                tags=memory.tags,
                metadata=memory.metadata,
            )

    def _delete_metadata(self, memory_id: str) -> None:
        """Delete memory metadata (placeholder)."""
        if not self._store:
            return
        if isinstance(self._store, SqliteMemoryStore):
            self._store.delete_long_term_metadata(memory_id)

    def __len__(self) -> int:
        """Get number of stored memories."""
        return self.get_size()

    def __repr__(self) -> str:
        """String representation."""
        backend = "Redis" if self._use_redis else "In-Memory"
        return f"LongTermMemory(backend={backend}, size={self.get_size()})"
