"""Base memory classes and types."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class Memory(BaseModel):
    """Base memory unit."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    type: MemoryType
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = 0
    # Default to "now" so callers don't have to provide it explicitly.
    last_accessed: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)


    def __repr__(self) -> str:
        """String representation."""
        return f"Memory(id={self.id}, type={self.type}, importance={self.importance})"


class MemoryConfig(BaseModel):
    """Configuration for memory system."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Capacity settings
    short_term_capacity: int = Field(default=20, ge=1)
    working_capacity: int = Field(default=5, ge=1)

    # Feature flags
    long_term_enabled: bool = True
    episodic_enabled: bool = True
    semantic_enabled: bool = True
    procedural_enabled: bool = True

    # Storage backends
    vector_db: Optional[str] = "pinecone"
    graph_db: Optional[str] = "neo4j"
    cache_db: Optional[str] = "redis"

    # Consolidation settings
    consolidation_enabled: bool = True
    consolidation_schedule: str = "0 2 * * *"  # Daily at 2 AM
    importance_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    retention_days: int = Field(default=365, ge=1)

    # Embedding settings
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

