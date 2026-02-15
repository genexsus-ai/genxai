"""Vector store implementations for long-term memory."""

from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from genxai.core.memory.base import Memory, MemoryType

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    async def store(
        self,
        memory: Memory,
        embedding: List[float],
    ) -> None:
        """Store a memory with its embedding.

        Args:
            memory: Memory to store
            embedding: Vector embedding of the memory
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            filters: Optional metadata filters

        Returns:
            List of (memory, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memories."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        pass

    async def aclose(self) -> None:
        """Close any underlying resources."""
        return


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store implementation."""

    def __init__(
        self,
        collection_name: str = "genxai_memories",
        persist_directory: Optional[str] = None,
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data (None for in-memory)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure ChromaDB client is initialized."""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            if self.persist_directory:
                self._client = chromadb.Client(
                    Settings(
                        persist_directory=self.persist_directory,
                        anonymized_telemetry=False,
                    )
                )
            else:
                self._client = chromadb.Client()

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "GenXAI agent memories"},
            )

            self._initialized = True
            logger.info(f"Initialized ChromaDB collection: {self.collection_name}")

        except ImportError:
            logger.error(
                "ChromaDB not installed. Install with: pip install chromadb"
            )
            raise RuntimeError("ChromaDB not available")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def store(
        self,
        memory: Memory,
        embedding: List[float],
    ) -> None:
        """Store a memory with its embedding."""
        await self._ensure_initialized()

        try:
            # Prepare metadata
            metadata = {
                "type": memory.type.value,
                "importance": memory.importance,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count,
                "tags": ",".join(memory.tags) if memory.tags else "",
                **memory.metadata,
            }

            # Store in ChromaDB
            self._collection.add(
                ids=[memory.id],
                embeddings=[embedding],
                documents=[str(memory.content)],
                metadatas=[metadata],
            )

            logger.debug(f"Stored memory {memory.id} in ChromaDB")

        except Exception as e:
            logger.error(f"Failed to store memory in ChromaDB: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories."""
        await self._ensure_initialized()

        try:
            # Build where clause for filters
            where = None
            if filters:
                where = {}
                for key, value in filters.items():
                    if key in ["type", "importance", "tags"]:
                        where[key] = value

            # Query ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
            )

            # Convert results to Memory objects
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    content = results["documents"][0][i]
                    distance = results["distances"][0][i] if "distances" in results else 0.0

                    # Reconstruct Memory object
                    memory = Memory(
                        id=memory_id,
                        type=MemoryType(metadata["type"]),
                        content=content,
                        metadata={k: v for k, v in metadata.items() if k not in ["type", "importance", "timestamp", "access_count", "tags"]},
                        timestamp=datetime.fromisoformat(metadata["timestamp"]),
                        importance=metadata["importance"],
                        access_count=metadata["access_count"],
                        last_accessed=datetime.now(),
                        tags=metadata["tags"].split(",") if metadata.get("tags") else [],
                    )

                    # Convert distance to similarity score (0-1)
                    similarity = 1.0 / (1.0 + distance)
                    memories.append((memory, similarity))

            logger.debug(f"Found {len(memories)} similar memories in ChromaDB")
            return memories

        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            return []

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        await self._ensure_initialized()

        try:
            self._collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory {memory_id} from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory from ChromaDB: {e}")
            return False

    async def clear(self) -> None:
        """Clear all memories."""
        await self._ensure_initialized()

        try:
            # Delete and recreate collection
            self._client.delete_collection(name=self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "GenXAI agent memories"},
            )
            logger.info(f"Cleared ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear ChromaDB: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        await self._ensure_initialized()

        try:
            count = self._collection.count()
            return {
                "backend": "chromadb",
                "collection": self.collection_name,
                "count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {"backend": "chromadb", "error": str(e)}

    async def aclose(self) -> None:
        """Close ChromaDB client if available."""
        if not self._client:
            return

        close_fn = getattr(self._client, "close", None)
        if close_fn:
            result = close_fn()
            if hasattr(result, "__await__"):
                await result

        self._client = None
        self._collection = None
        self._initialized = False


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation."""

    def __init__(
        self,
        index_name: str = "genxai-memories",
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        dimension: int = 1536,
    ) -> None:
        """Initialize Pinecone vector store.

        Args:
            index_name: Name of the Pinecone index
            api_key: Pinecone API key (or set PINECONE_API_KEY env var)
            environment: Pinecone environment (or set PINECONE_ENVIRONMENT env var)
            dimension: Vector dimension
        """
        self.index_name = index_name
        self.api_key = api_key
        self.environment = environment
        self.dimension = dimension
        self._index = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure Pinecone client is initialized."""
        if self._initialized:
            return

        try:
            import pinecone
            import os

            # Get API key and environment
            api_key = self.api_key or os.getenv("PINECONE_API_KEY")
            environment = self.environment or os.getenv("PINECONE_ENVIRONMENT")

            if not api_key or not environment:
                raise ValueError(
                    "Pinecone API key and environment required. "
                    "Set PINECONE_API_KEY and PINECONE_ENVIRONMENT env vars."
                )

            # Initialize Pinecone
            pinecone.init(api_key=api_key, environment=environment)

            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                )
                logger.info(f"Created Pinecone index: {self.index_name}")

            # Connect to index
            self._index = pinecone.Index(self.index_name)
            self._initialized = True
            logger.info(f"Initialized Pinecone index: {self.index_name}")

        except ImportError:
            logger.error(
                "Pinecone not installed. Install with: pip install pinecone-client"
            )
            raise RuntimeError("Pinecone not available")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    async def store(
        self,
        memory: Memory,
        embedding: List[float],
    ) -> None:
        """Store a memory with its embedding."""
        await self._ensure_initialized()

        try:
            # Prepare metadata
            metadata = {
                "type": memory.type.value,
                "content": str(memory.content),
                "importance": memory.importance,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count,
                "tags": ",".join(memory.tags) if memory.tags else "",
                **memory.metadata,
            }

            # Store in Pinecone
            self._index.upsert(
                vectors=[(memory.id, embedding, metadata)]
            )

            logger.debug(f"Stored memory {memory.id} in Pinecone")

        except Exception as e:
            logger.error(f"Failed to store memory in Pinecone: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories."""
        await self._ensure_initialized()

        try:
            # Build filter
            filter_dict = None
            if filters:
                filter_dict = {}
                for key, value in filters.items():
                    if key in ["type", "importance", "tags"]:
                        filter_dict[key] = value

            # Query Pinecone
            results = self._index.query(
                vector=query_embedding,
                top_k=limit,
                filter=filter_dict,
                include_metadata=True,
            )

            # Convert results to Memory objects
            memories = []
            for match in results.matches:
                metadata = match.metadata

                # Reconstruct Memory object
                memory = Memory(
                    id=match.id,
                    type=MemoryType(metadata["type"]),
                    content=metadata["content"],
                    metadata={k: v for k, v in metadata.items() if k not in ["type", "content", "importance", "timestamp", "access_count", "tags"]},
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    importance=metadata["importance"],
                    access_count=metadata["access_count"],
                    last_accessed=datetime.now(),
                    tags=metadata["tags"].split(",") if metadata.get("tags") else [],
                )

                memories.append((memory, match.score))

            logger.debug(f"Found {len(memories)} similar memories in Pinecone")
            return memories

        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        await self._ensure_initialized()

        try:
            self._index.delete(ids=[memory_id])
            logger.debug(f"Deleted memory {memory_id} from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory from Pinecone: {e}")
            return False

    async def clear(self) -> None:
        """Clear all memories."""
        await self._ensure_initialized()

        try:
            self._index.delete(delete_all=True)
            logger.info(f"Cleared Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to clear Pinecone: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        await self._ensure_initialized()

        try:
            stats = self._index.describe_index_stats()
            return {
                "backend": "pinecone",
                "index": self.index_name,
                "dimension": self.dimension,
                "total_vector_count": stats.total_vector_count,
                "namespaces": stats.namespaces,
            }
        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            return {"backend": "pinecone", "error": str(e)}

    async def aclose(self) -> None:
        """Close Pinecone index if available."""
        if not self._index:
            return

        close_fn = getattr(self._index, "close", None)
        if close_fn:
            result = close_fn()
            if hasattr(result, "__await__"):
                await result

        self._index = None
        self._initialized = False


class VectorStoreFactory:
    """Factory for creating vector stores."""

    _stores = {
        "chromadb": ChromaVectorStore,
        "pinecone": PineconeVectorStore,
    }

    @classmethod
    def create(
        cls,
        backend: str,
        **kwargs
    ) -> VectorStore:
        """Create a vector store instance.

        Args:
            backend: Vector store backend ("chromadb", "pinecone")
            **kwargs: Backend-specific arguments

        Returns:
            VectorStore instance

        Raises:
            ValueError: If backend is not supported
        """
        if backend not in cls._stores:
            raise ValueError(
                f"Unsupported vector store backend: {backend}. "
                f"Supported: {list(cls._stores.keys())}"
            )

        store_class = cls._stores[backend]
        return store_class(**kwargs)

    @classmethod
    def register(cls, name: str, store_class: type) -> None:
        """Register a custom vector store.

        Args:
            name: Name of the vector store
            store_class: Vector store class
        """
        cls._stores[name] = store_class
        logger.info(f"Registered vector store: {name}")

    @classmethod
    def list_backends(cls) -> List[str]:
        """List available vector store backends."""
        return list(cls._stores.keys())
