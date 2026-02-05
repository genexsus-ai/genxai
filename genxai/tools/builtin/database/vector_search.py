"""Vector search tool for semantic similarity search."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class VectorSearchTool(Tool):
    """Perform semantic similarity search in vector databases."""

    def __init__(self) -> None:
        """Initialize vector search tool."""
        metadata = ToolMetadata(
            name="vector_search",
            description="Search vector databases for semantic similarity (supports in-memory vectors)",
            category=ToolCategory.DATABASE,
            tags=["vector", "semantic", "search", "similarity", "embeddings"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="query",
                type="string",
                description="Search query text",
                required=True,
            ),
            ToolParameter(
                name="vectors",
                type="object",
                description="Dictionary of id:vector pairs to search (for in-memory search)",
                required=True,
            ),
            ToolParameter(
                name="top_k",
                type="number",
                description="Number of top results to return",
                required=False,
                default=5,
                min_value=1,
                max_value=100,
            ),
            ToolParameter(
                name="threshold",
                type="number",
                description="Minimum similarity threshold (0-1)",
                required=False,
                default=0.0,
                min_value=0.0,
                max_value=1.0,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        query: str,
        vectors: Dict[str, List[float]],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> Dict[str, Any]:
        """Execute vector search.

        Args:
            query: Search query
            vectors: Dictionary of vectors to search
            top_k: Number of results
            threshold: Similarity threshold

        Returns:
            Dictionary containing search results
        """
        result: Dict[str, Any] = {
            "query": query,
            "success": False,
        }

        try:
            # Simple in-memory vector search using cosine similarity
            # In production, this would connect to Pinecone, Weaviate, etc.
            
            # For demo purposes, we'll use a simple similarity calculation
            # Assuming query is already a vector or we have a simple embedding
            
            # Convert query to simple vector (character-based for demo)
            query_vector = self._text_to_simple_vector(query)
            
            # Calculate similarities
            similarities = []
            for doc_id, doc_vector in vectors.items():
                similarity = self._cosine_similarity(query_vector, doc_vector)
                if similarity >= threshold:
                    similarities.append({
                        "id": doc_id,
                        "similarity": similarity,
                    })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top k
            top_results = similarities[:top_k]
            
            result.update({
                "results": top_results,
                "count": len(top_results),
                "total_searched": len(vectors),
                "success": True,
            })

        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Vector search completed: success={result['success']}")
        return result

    def _text_to_simple_vector(self, text: str, dim: int = 128) -> List[float]:
        """Convert text to simple vector (demo implementation).

        Args:
            text: Input text
            dim: Vector dimension

        Returns:
            Vector representation
        """
        # Simple character-based vectorization for demo
        vector = [0.0] * dim
        for i, char in enumerate(text[:dim]):
            vector[i] = ord(char) / 255.0
        return vector

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        # Ensure same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
