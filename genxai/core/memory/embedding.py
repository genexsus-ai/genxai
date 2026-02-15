"""Embedding service for memory vectorization."""

from typing import List, Optional, Union
from abc import ABC, abstractmethod
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.

        Args:
            text: Single text string or list of texts

        Returns:
            Single embedding or list of embeddings
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass

    async def aclose(self) -> None:
        """Close any underlying async client resources."""
        return


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service."""

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize OpenAI embedding service.

        Args:
            model: OpenAI embedding model
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._initialized = False

        # Model dimensions
        self._dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

    async def _ensure_initialized(self) -> None:
        """Ensure OpenAI client is initialized."""
        if self._initialized:
            return

        try:
            from openai import AsyncOpenAI

            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY env var."
                )

            self._client = AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Initialized OpenAI embedding service: {self.model}")

        except ImportError:
            logger.error(
                "OpenAI not installed. Install with: pip install openai"
            )
            raise RuntimeError("OpenAI not available")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text."""
        await self._ensure_initialized()

        try:
            # Handle single text vs batch
            is_single = isinstance(text, str)
            texts = [text] if is_single else text

            # Generate embeddings
            response = await self._client.embeddings.create(
                model=self.model,
                input=texts,
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            # Return single embedding or list
            return embeddings[0] if is_single else embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimensions.get(self.model, 1536)

    async def aclose(self) -> None:
        """Close OpenAI client if initialized."""
        if not self._client:
            return

        close_fn = getattr(self._client, "aclose", None)
        if close_fn:
            await close_fn()
        else:
            close_fn = getattr(self._client, "close", None)
            if close_fn:
                result = close_fn()
                if hasattr(result, "__await__"):
                    await result

        self._client = None
        self._initialized = False


class LocalEmbeddingService(EmbeddingService):
    """Local embedding service using sentence-transformers."""

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ) -> None:
        """Initialize local embedding service.

        Args:
            model: Sentence-transformers model name
            device: Device to use ('cpu', 'cuda', or None for auto)
        """
        self.model_name = model
        self.device = device
        self._model = None
        self._initialized = False

        # Common model dimensions
        self._dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "all-MiniLM-L12-v2": 384,
        }

    async def _ensure_initialized(self) -> None:
        """Ensure model is loaded."""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            logger.info(f"Initialized local embedding model: {self.model_name}")

        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise RuntimeError("sentence-transformers not available")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text."""
        await self._ensure_initialized()

        try:
            # Handle single text vs batch
            is_single = isinstance(text, str)
            texts = [text] if is_single else text

            # Generate embeddings
            embeddings = self._model.encode(texts, convert_to_numpy=True)

            # Convert to list
            embeddings = embeddings.tolist()

            # Return single embedding or list
            return embeddings[0] if is_single else embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self._initialized and self._model:
            return self._model.get_sentence_embedding_dimension()
        return self._dimensions.get(self.model_name, 384)


class CohereEmbeddingService(EmbeddingService):
    """Cohere embedding service."""

    def __init__(
        self,
        model: str = "embed-english-v3.0",
        api_key: Optional[str] = None,
        input_type: str = "search_document",
    ) -> None:
        """Initialize Cohere embedding service.

        Args:
            model: Cohere embedding model
            api_key: Cohere API key (or set COHERE_API_KEY env var)
            input_type: Input type ('search_document', 'search_query', 'classification', 'clustering')
        """
        self.model = model
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self.input_type = input_type
        self._client = None
        self._initialized = False

        # Model dimensions
        self._dimensions = {
            "embed-english-v3.0": 1024,
            "embed-english-light-v3.0": 384,
            "embed-multilingual-v3.0": 1024,
        }

    async def _ensure_initialized(self) -> None:
        """Ensure Cohere client is initialized."""
        if self._initialized:
            return

        try:
            import cohere

            if not self.api_key:
                raise ValueError(
                    "Cohere API key required. Set COHERE_API_KEY env var."
                )

            self._client = cohere.AsyncClient(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Initialized Cohere embedding service: {self.model}")

        except ImportError:
            logger.error(
                "Cohere not installed. Install with: pip install cohere"
            )
            raise RuntimeError("Cohere not available")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere: {e}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text."""
        await self._ensure_initialized()

        try:
            # Handle single text vs batch
            is_single = isinstance(text, str)
            texts = [text] if is_single else text

            # Generate embeddings
            response = await self._client.embed(
                texts=texts,
                model=self.model,
                input_type=self.input_type,
            )

            # Extract embeddings
            embeddings = response.embeddings

            # Return single embedding or list
            return embeddings[0] if is_single else embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimensions.get(self.model, 1024)

    async def aclose(self) -> None:
        """Close Cohere client if initialized."""
        if not self._client:
            return

        close_fn = getattr(self._client, "close", None)
        if close_fn:
            result = close_fn()
            if hasattr(result, "__await__"):
                await result

        self._client = None
        self._initialized = False


class EmbeddingServiceFactory:
    """Factory for creating embedding services."""

    _services = {
        "openai": OpenAIEmbeddingService,
        "local": LocalEmbeddingService,
        "cohere": CohereEmbeddingService,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        **kwargs
    ) -> EmbeddingService:
        """Create an embedding service instance.

        Args:
            provider: Embedding provider ("openai", "local", "cohere")
            **kwargs: Provider-specific arguments

        Returns:
            EmbeddingService instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._services:
            raise ValueError(
                f"Unsupported embedding provider: {provider}. "
                f"Supported: {list(cls._services.keys())}"
            )

        service_class = cls._services[provider]
        return service_class(**kwargs)

    @classmethod
    def register(cls, name: str, service_class: type) -> None:
        """Register a custom embedding service.

        Args:
            name: Name of the service
            service_class: Embedding service class
        """
        cls._services[name] = service_class
        logger.info(f"Registered embedding service: {name}")

    @classmethod
    def list_providers(cls) -> List[str]:
        """List available embedding providers."""
        return list(cls._services.keys())
