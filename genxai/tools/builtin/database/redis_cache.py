"""Redis cache tool for caching operations."""

from typing import Any, Dict, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class RedisCacheTool(Tool):
    """Interact with Redis cache for get/set/delete operations."""

    def __init__(self) -> None:
        """Initialize Redis cache tool."""
        metadata = ToolMetadata(
            name="redis_cache",
            description="Perform Redis cache operations (get, set, delete, exists)",
            category=ToolCategory.DATABASE,
            tags=["redis", "cache", "key-value", "memory", "storage"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="Cache operation to perform",
                required=True,
                enum=["get", "set", "delete", "exists", "keys", "ttl"],
            ),
            ToolParameter(
                name="key",
                type="string",
                description="Cache key",
                required=True,
            ),
            ToolParameter(
                name="value",
                type="string",
                description="Value to set (for set operation)",
                required=False,
            ),
            ToolParameter(
                name="ttl",
                type="number",
                description="Time to live in seconds (for set operation)",
                required=False,
            ),
            ToolParameter(
                name="host",
                type="string",
                description="Redis host",
                required=False,
                default="localhost",
            ),
            ToolParameter(
                name="port",
                type="number",
                description="Redis port",
                required=False,
                default=6379,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        operation: str,
        key: str,
        value: Optional[str] = None,
        ttl: Optional[int] = None,
        host: str = "localhost",
        port: int = 6379,
    ) -> Dict[str, Any]:
        """Execute Redis cache operation.

        Args:
            operation: Operation to perform
            key: Cache key
            value: Value to set
            ttl: Time to live
            host: Redis host
            port: Redis port

        Returns:
            Dictionary containing operation results
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis package not installed. Install with: pip install redis"
            )

        result: Dict[str, Any] = {
            "operation": operation,
            "key": key,
            "success": False,
        }

        try:
            # Connect to Redis
            client = redis.Redis(host=host, port=port, decode_responses=True)

            if operation == "get":
                cached_value = client.get(key)
                result.update({
                    "value": cached_value,
                    "exists": cached_value is not None,
                    "success": True,
                })

            elif operation == "set":
                if value is None:
                    raise ValueError("value parameter required for set operation")
                
                if ttl:
                    client.setex(key, ttl, value)
                else:
                    client.set(key, value)
                
                result.update({
                    "value": value,
                    "ttl": ttl,
                    "success": True,
                })

            elif operation == "delete":
                deleted_count = client.delete(key)
                result.update({
                    "deleted": deleted_count > 0,
                    "success": True,
                })

            elif operation == "exists":
                exists = client.exists(key) > 0
                result.update({
                    "exists": exists,
                    "success": True,
                })

            elif operation == "keys":
                # Use key as pattern
                matching_keys = client.keys(key)
                result.update({
                    "keys": matching_keys,
                    "count": len(matching_keys),
                    "success": True,
                })

            elif operation == "ttl":
                ttl_value = client.ttl(key)
                result.update({
                    "ttl": ttl_value,
                    "exists": ttl_value >= 0,
                    "success": True,
                })

        except redis.RedisError as e:
            result["error"] = f"Redis error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Redis {operation} completed: success={result['success']}")
        return result
