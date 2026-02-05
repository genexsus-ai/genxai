"""Unit tests for performance cache utilities."""

import asyncio
import time

from genxai.performance.cache import CacheManager, MemoryCache, cached, LRUCache


def test_memory_cache_basic() -> None:
    cache = MemoryCache()
    cache.set("alpha", "value")
    assert cache.get("alpha") == "value"
    cache.delete("alpha")
    assert cache.get("alpha") is None


def test_memory_cache_ttl_expiry() -> None:
    cache = MemoryCache()
    cache.set("beta", "value", ttl=1)
    assert cache.get("beta") == "value"
    time.sleep(1.2)
    assert cache.get("beta") is None


def test_cache_manager_key_determinism() -> None:
    cache = CacheManager(MemoryCache())
    key1 = cache.cache_key("prefix", 1, b=2)
    key2 = cache.cache_key("prefix", 1, b=2)
    assert key1 == key2


def test_lru_cache_eviction() -> None:
    lru = LRUCache(capacity=2)
    lru.set("a", 1)
    lru.set("b", 2)
    lru.get("a")
    lru.set("c", 3)
    assert lru.get("b") is None
    assert lru.get("a") == 1
    assert lru.get("c") == 3


def test_cached_decorator_sync() -> None:
    calls = {"count": 0}

    @cached("sync")
    def compute(x: int) -> int:
        calls["count"] += 1
        return x + 1

    assert compute(1) == 2
    assert compute(1) == 2
    assert calls["count"] == 1


def test_cached_decorator_async() -> None:
    calls = {"count": 0}

    @cached("async")
    async def compute(x: int) -> int:
        calls["count"] += 1
        return x + 1

    async def run() -> None:
        assert await compute(2) == 3
        assert await compute(2) == 3
        assert calls["count"] == 1

    asyncio.run(run())
