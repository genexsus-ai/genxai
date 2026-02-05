"""Working memory implementation for active processing."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from collections import deque

from genxai.core.memory.base import Memory, MemoryType

logger = logging.getLogger(__name__)


class WorkingMemory:
    """Working memory for active processing and temporary storage.
    
    Working memory holds information that is currently being processed:
    - Current task context
    - Intermediate results
    - Active goals
    - Temporary computations
    
    Has limited capacity and items are automatically evicted when full.
    """

    def __init__(
        self,
        capacity: int = 5,
    ) -> None:
        """Initialize working memory.

        Args:
            capacity: Maximum number of items to hold
        """
        self._capacity = capacity
        self._items: deque = deque(maxlen=capacity)
        self._item_map: Dict[str, Any] = {}  # id -> item for fast lookup
        
        logger.info(f"Initialized working memory with capacity {capacity}")

    def add(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an item to working memory.

        Args:
            key: Item key/identifier
            value: Item value
            metadata: Optional metadata
        """
        item = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
        }

        # Remove old item with same key if exists
        if key in self._item_map:
            self.remove(key)

        # Add new item
        self._items.append(item)
        self._item_map[key] = item

        # If capacity exceeded, oldest item was automatically removed by deque
        # Update item_map accordingly
        if len(self._items) < len(self._item_map):
            # Find and remove evicted items from map
            current_keys = {item["key"] for item in self._items}
            evicted_keys = set(self._item_map.keys()) - current_keys
            for evicted_key in evicted_keys:
                del self._item_map[evicted_key]
                logger.debug(f"Evicted item from working memory: {evicted_key}")

        logger.debug(f"Added to working memory: {key}")

    def get(self, key: str) -> Optional[Any]:
        """Get an item from working memory.

        Args:
            key: Item key

        Returns:
            Item value if found, None otherwise
        """
        item = self._item_map.get(key)
        if item:
            return item["value"]
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all items in working memory.

        Returns:
            List of all items
        """
        return list(self._items)

    def get_recent(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent items.

        Args:
            n: Number of items to retrieve

        Returns:
            List of recent items
        """
        return list(self._items)[-n:] if len(self._items) >= n else list(self._items)

    def remove(self, key: str) -> bool:
        """Remove an item from working memory.

        Args:
            key: Item key

        Returns:
            True if removed, False if not found
        """
        if key not in self._item_map:
            return False

        # Remove from deque
        self._items = deque(
            (item for item in self._items if item["key"] != key),
            maxlen=self._capacity
        )

        # Remove from map
        del self._item_map[key]

        logger.debug(f"Removed from working memory: {key}")
        return True

    def clear(self) -> None:
        """Clear all items from working memory."""
        count = len(self._items)
        self._items.clear()
        self._item_map.clear()
        logger.info(f"Cleared {count} items from working memory")

    def contains(self, key: str) -> bool:
        """Check if key exists in working memory.

        Args:
            key: Item key

        Returns:
            True if exists, False otherwise
        """
        return key in self._item_map

    def get_size(self) -> int:
        """Get current number of items.

        Returns:
            Number of items
        """
        return len(self._items)

    def get_capacity(self) -> int:
        """Get maximum capacity.

        Returns:
            Capacity
        """
        return self._capacity

    def is_full(self) -> bool:
        """Check if working memory is full.

        Returns:
            True if full, False otherwise
        """
        return len(self._items) >= self._capacity

    def get_stats(self) -> Dict[str, Any]:
        """Get working memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._items:
            return {
                "size": 0,
                "capacity": self._capacity,
                "utilization": 0.0,
            }

        return {
            "size": len(self._items),
            "capacity": self._capacity,
            "utilization": len(self._items) / self._capacity,
            "oldest_item": self._items[0]["timestamp"].isoformat(),
            "newest_item": self._items[-1]["timestamp"].isoformat(),
            "keys": [item["key"] for item in self._items],
        }

    def __len__(self) -> int:
        """Get number of items."""
        return len(self._items)

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._item_map

    def __repr__(self) -> str:
        """String representation."""
        return f"WorkingMemory(size={len(self._items)}/{self._capacity})"
