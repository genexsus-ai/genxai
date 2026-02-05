"""Short-term memory implementation with LRU eviction."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import OrderedDict
import logging

from genxai.core.memory.base import Memory, MemoryType, MemoryConfig

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Short-term memory with limited capacity and LRU eviction.
    
    This memory type stores recent interactions and automatically evicts
    the least recently used items when capacity is reached.
    """

    def __init__(self, config: Optional[MemoryConfig] = None, capacity: Optional[int] = None) -> None:
        """Initialize short-term memory.

        Args:
            config: Memory configuration (uses defaults if not provided)
            capacity: Override capacity (for backward compatibility)
        """
        self.config = config or MemoryConfig()
        self.capacity = capacity if capacity is not None else self.config.short_term_capacity
        
        # Use OrderedDict for LRU behavior
        self._memories: OrderedDict[str, Memory] = OrderedDict()
        self._access_count = 0
        
        logger.info(f"Initialized short-term memory with capacity: {self.capacity}")

    def store(self, memory: Memory) -> None:
        """Store a memory item.

        If capacity is reached, evicts the least recently used item.

        Args:
            memory: Memory to store
        """
        # If memory already exists, remove it (will be re-added at end)
        if memory.id in self._memories:
            del self._memories[memory.id]
        
        # If at capacity, remove oldest (least recently used)
        if len(self._memories) >= self.capacity:
            oldest_id = next(iter(self._memories))
            evicted = self._memories.pop(oldest_id)
            logger.debug(f"Evicted memory {oldest_id} (importance: {evicted.importance})")
        
        # Add new memory at end (most recently used)
        self._memories[memory.id] = memory
        logger.debug(f"Stored memory {memory.id} in short-term memory")

    def retrieve(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID.

        Accessing a memory moves it to the end (most recently used).

        Args:
            memory_id: ID of memory to retrieve

        Returns:
            Memory if found, None otherwise
        """
        if memory_id not in self._memories:
            return None
        
        # Move to end (mark as recently used)
        memory = self._memories.pop(memory_id)
        self._memories[memory_id] = memory
        
        # Update access tracking
        memory.access_count += 1
        memory.last_accessed = datetime.now()
        self._access_count += 1
        
        logger.debug(f"Retrieved memory {memory_id} (access count: {memory.access_count})")
        return memory

    def retrieve_recent(self, limit: int = 10) -> List[Memory]:
        """Retrieve the most recent memories.

        Args:
            limit: Maximum number of memories to retrieve

        Returns:
            List of recent memories (most recent first)
        """
        # Get last N items (most recent)
        recent_items = list(self._memories.values())[-limit:]
        
        # Reverse to get most recent first
        recent_items.reverse()
        
        logger.debug(f"Retrieved {len(recent_items)} recent memories")
        return recent_items

    def retrieve_by_importance(self, threshold: float = 0.5, limit: int = 10) -> List[Memory]:
        """Retrieve memories above an importance threshold.

        Args:
            threshold: Minimum importance score (0.0 to 1.0)
            limit: Maximum number of memories to retrieve

        Returns:
            List of important memories (sorted by importance, descending)
        """
        # Filter by importance
        important = [m for m in self._memories.values() if m.importance >= threshold]
        
        # Sort by importance (descending)
        important.sort(key=lambda m: m.importance, reverse=True)
        
        # Limit results
        result = important[:limit]
        
        logger.debug(
            f"Retrieved {len(result)} memories with importance >= {threshold}"
        )
        return result

    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """Search memories by content.

        Simple text-based search. For semantic search, use long-term memory.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        query_lower = query.lower()
        matches = []
        
        for memory in self._memories.values():
            # Convert content to string for searching
            content_str = str(memory.content).lower()
            
            if query_lower in content_str:
                matches.append(memory)
        
        # Sort by recency (most recent first)
        matches.reverse()
        
        # Limit results
        result = matches[:limit]
        
        logger.debug(f"Found {len(result)} memories matching '{query}'")
        return result

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        if memory_id in self._memories:
            del self._memories[memory_id]
            logger.debug(f"Deleted memory {memory_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all memories."""
        count = len(self._memories)
        self._memories.clear()
        logger.info(f"Cleared {count} memories from short-term memory")

    def get_size(self) -> int:
        """Get current number of stored memories.

        Returns:
            Number of memories
        """
        return len(self._memories)

    def get_capacity(self) -> int:
        """Get maximum capacity.

        Returns:
            Maximum number of memories
        """
        return self.capacity

    def is_full(self) -> bool:
        """Check if memory is at capacity.

        Returns:
            True if at capacity
        """
        return len(self._memories) >= self.capacity

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._memories:
            return {
                "size": 0,
                "capacity": self.capacity,
                "utilization": 0.0,
                "total_accesses": self._access_count,
                "avg_importance": 0.0,
                "avg_access_count": 0.0,
            }
        
        memories = list(self._memories.values())
        
        return {
            "size": len(memories),
            "capacity": self.capacity,
            "utilization": len(memories) / self.capacity,
            "total_accesses": self._access_count,
            "avg_importance": sum(m.importance for m in memories) / len(memories),
            "avg_access_count": sum(m.access_count for m in memories) / len(memories),
            "oldest_memory": memories[0].timestamp.isoformat() if memories else None,
            "newest_memory": memories[-1].timestamp.isoformat() if memories else None,
        }

    def __len__(self) -> int:
        """Get number of stored memories."""
        return len(self._memories)

    def __contains__(self, memory_id: str) -> bool:
        """Check if memory exists."""
        return memory_id in self._memories

    async def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add content to short-term memory.
        
        Args:
            content: Content to store
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        import uuid
        from genxai.core.memory.base import Memory, MemoryType
        from datetime import datetime
        
        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            type=MemoryType.SHORT_TERM,
            importance=0.5,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        self.store(memory)
        return memory.id
    
    async def get_context(self, max_tokens: int = 4000) -> str:
        """Get formatted context string for LLM.
        
        Args:
            max_tokens: Maximum tokens to include
            
        Returns:
            Formatted context string
        """
        recent = self.retrieve_recent(limit=10)
        
        if not recent:
            return ""
        
        context_parts = ["Recent context:"]
        for memory in recent:
            # Keep this robust: if content is a dict, stringify it so unit tests
            # can find values like "Hello" in the context.
            if isinstance(memory.content, dict):
                context_parts.append(f"- {memory.content}")
            else:
                context_parts.append(f"- {memory.content}")
        
        return "\n".join(context_parts)
    
    async def clear_async(self) -> None:
        """Clear all memories (async version)."""
        count = len(self._memories)
        self._memories.clear()
        logger.info(f"Cleared {count} memories from short-term memory")
    
    @property
    def memories(self) -> List[Memory]:
        """Get all memories as a list."""
        return list(self._memories.values())

    def __repr__(self) -> str:
        """String representation."""
        return f"ShortTermMemory(size={len(self._memories)}, capacity={self.capacity})"
