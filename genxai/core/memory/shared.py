"""Shared memory bus for cross-agent collaboration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class SharedMemoryEntry:
    key: str
    value: Any
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedMemoryBus:
    """In-memory shared memory store with pub/sub hooks."""

    def __init__(self) -> None:
        self._store: Dict[str, SharedMemoryEntry] = {}
        self._subscribers: Dict[str, List[Callable[[SharedMemoryEntry], Awaitable[None]]]] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        async with self._lock:
            entry = SharedMemoryEntry(key=key, value=value, metadata=metadata or {})
            self._store[key] = entry
            await self._notify(key, entry)

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        return entry.value if entry else default

    def list_keys(self) -> List[str]:
        return list(self._store.keys())

    def subscribe(
        self, key: str, callback: Callable[[SharedMemoryEntry], Awaitable[None]]
    ) -> None:
        self._subscribers.setdefault(key, []).append(callback)

    async def _notify(self, key: str, entry: SharedMemoryEntry) -> None:
        for callback in self._subscribers.get(key, []):
            try:
                await callback(entry)
            except Exception as exc:
                logger.error("Shared memory notify error for %s: %s", key, exc)