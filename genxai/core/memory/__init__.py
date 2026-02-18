"""Memory system for GenXAI agents."""

from genxai.core.memory.base import Memory, MemoryType, MemoryConfig
from genxai.core.memory.short_term import ShortTermMemory
from genxai.core.memory.shared import SharedMemoryBus
from genxai.core.memory.long_term import LongTermMemory
from genxai.core.memory.manager import MemorySystem
from genxai.core.memory.persistence import MemoryPersistenceConfig, JsonMemoryStore
from genxai.core.memory.backends import (
    MemoryBackendPlugin,
    MemoryBackendRegistry,
    RedisMemoryBackendPlugin,
    SqliteMemoryBackendPlugin,
    Neo4jMemoryBackendPlugin,
)

__all__ = [
    "Memory",
    "MemoryType",
    "MemoryConfig",
    "ShortTermMemory",
    "LongTermMemory",
    "MemorySystem",
    "MemoryPersistenceConfig",
    "JsonMemoryStore",
    "MemoryBackendPlugin",
    "MemoryBackendRegistry",
    "RedisMemoryBackendPlugin",
    "SqliteMemoryBackendPlugin",
    "Neo4jMemoryBackendPlugin",
]
