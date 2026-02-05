"""Caching system for GenXAI performance optimization."""

import hashlib
import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
import time
from datetime import timedelta


class CacheBackend:
    """Base cache backend."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        raise NotImplementedError
    
    def delete(self, key: str):
        """Delete value from cache."""
        raise NotImplementedError
    
    def clear(self):
        """Clear all cache."""
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check expiry
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                self.delete(key)
                return None
        
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        self._cache[key] = value
        
        if ttl:
            self._expiry[key] = time.time() + ttl
    
    def delete(self, key: str):
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._expiry.clear()


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis
            self.client = redis.from_url(redis_url)
        except ImportError:
            raise ImportError("Redis not installed. Install with: pip install redis")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = self.client.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        serialized = pickle.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialized)
        else:
            self.client.set(key, serialized)
    
    def delete(self, key: str):
        """Delete value from cache."""
        self.client.delete(key)
    
    def clear(self):
        """Clear all cache."""
        self.client.flushdb()


class CacheManager:
    """Manage caching for different components."""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key."""
        # Create deterministic key from arguments
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get from cache."""
        return self.backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set in cache."""
        self.backend.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete from cache."""
        self.backend.delete(key)
    
    def clear(self):
        """Clear cache."""
        self.backend.clear()


# Global cache manager
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager."""
    global _cache_manager
    
    if _cache_manager is None:
        import os
        backend_type = os.getenv("CACHE_BACKEND", "memory")
        
        if backend_type == "redis":
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            backend = RedisCache(redis_url)
        else:
            backend = MemoryCache()
        
        _cache_manager = CacheManager(backend)
    
    return _cache_manager


def cached(prefix: str, ttl: Optional[int] = 3600):
    """Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: 1 hour)
        
    Usage:
        @cached("llm_response", ttl=3600)
        async def get_llm_response(prompt):
            return await llm.generate(prompt)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = cache.cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = cache.cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LRUCache:
    """LRU (Least Recently Used) cache implementation."""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = {}
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get value and update access order."""
        if key not in self.cache:
            return None
        
        # Update access order
        self.access_order.remove(key)
        self.access_order.append(key)
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value and manage capacity."""
        if key in self.cache:
            # Update existing
            self.access_order.remove(key)
        elif len(self.cache) >= self.capacity:
            # Evict least recently used
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()
