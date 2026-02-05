"""Performance optimization utilities for GenXAI."""

from genxai.performance.cache import (
    CacheManager,
    MemoryCache,
    RedisCache,
    LRUCache,
    cached,
    get_cache_manager
)

from genxai.performance.pooling import (
    ConnectionPool,
    DatabaseConnectionPool,
    HTTPConnectionPool,
    VectorStoreConnectionPool,
    get_db_pool,
    get_http_pool,
    get_vector_pool
)

__all__ = [
    # Caching
    "CacheManager",
    "MemoryCache",
    "RedisCache",
    "LRUCache",
    "cached",
    "get_cache_manager",
    
    # Connection pooling
    "ConnectionPool",
    "DatabaseConnectionPool",
    "HTTPConnectionPool",
    "VectorStoreConnectionPool",
    "get_db_pool",
    "get_http_pool",
    "get_vector_pool",
]
