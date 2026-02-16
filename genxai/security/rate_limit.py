"""Rate limiting for GenXAI using token bucket algorithm."""

import time
import asyncio
from typing import Optional, Dict
from functools import wraps
from dataclasses import dataclass
import os


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int


# Rate limit tiers
RATE_LIMITS = {
    "free": RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=1000,
    ),
    "pro": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
    ),
    "enterprise": RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        requests_per_day=100000,
    ),
}


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, rate: float, capacity: int):
        """Initialize token bucket.
        
        Args:
            rate: Tokens per second
            capacity: Bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if rate limited
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            # Check if enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def get_remaining(self) -> int:
        """Get remaining tokens.
        
        Returns:
            Number of remaining tokens
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            
            return int(tokens)


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, storage: str = "memory"):
        """Initialize rate limiter.
        
        Args:
            storage: Storage backend (memory or redis)
        """
        self.storage = storage
        self.buckets: Dict[str, Dict[str, TokenBucket]] = {}
        
        # Try to import Redis if using redis storage
        if storage == "redis":
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self.redis_client = redis.from_url(redis_url)
            except ImportError:
                print("Redis not available, falling back to memory storage")
                self.storage = "memory"
    
    async def check_rate_limit(
        self,
        key: str,
        tier: str = "free",
        cost: int = 1
    ) -> bool:
        """Check if request is within rate limit.
        
        Args:
            key: User ID or API key
            tier: Rate limit tier (free, pro, enterprise)
            cost: Cost in tokens (default: 1)
            
        Returns:
            True if within limit, False if rate limited
        """
        config = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        
        # Check minute limit
        minute_key = f"{key}:minute"
        if not await self._check_bucket(
            minute_key,
            rate=config.requests_per_minute / 60,
            capacity=config.requests_per_minute,
            cost=cost
        ):
            return False
        
        # Check hour limit
        hour_key = f"{key}:hour"
        if not await self._check_bucket(
            hour_key,
            rate=config.requests_per_hour / 3600,
            capacity=config.requests_per_hour,
            cost=cost
        ):
            return False
        
        # Check day limit
        day_key = f"{key}:day"
        if not await self._check_bucket(
            day_key,
            rate=config.requests_per_day / 86400,
            capacity=config.requests_per_day,
            cost=cost
        ):
            return False
        
        return True
    
    async def _check_bucket(
        self,
        key: str,
        rate: float,
        capacity: int,
        cost: int
    ) -> bool:
        """Check token bucket.
        
        Args:
            key: Bucket key
            rate: Tokens per second
            capacity: Bucket capacity
            cost: Tokens to consume
            
        Returns:
            True if tokens consumed, False if rate limited
        """
        if self.storage == "memory":
            # Get or create bucket
            if key not in self.buckets:
                self.buckets[key] = {}
            
            if "bucket" not in self.buckets[key]:
                self.buckets[key]["bucket"] = TokenBucket(rate, capacity)
            
            bucket = self.buckets[key]["bucket"]
            return await bucket.consume(cost)
        
        elif self.storage == "redis":
            # Redis-based rate limiting using Lua script
            # This is a simplified version
            return await self._check_redis_bucket(key, rate, capacity, cost)
        
        return True
    
    async def _check_redis_bucket(
        self,
        key: str,
        rate: float,
        capacity: int,
        cost: int
    ) -> bool:
        """Check rate limit using Redis.
        
        Args:
            key: Bucket key
            rate: Tokens per second
            capacity: Bucket capacity
            cost: Tokens to consume
            
        Returns:
            True if within limit, False if rate limited
        """
        # Simplified Redis implementation
        # In production, use a Lua script for atomicity
        try:
            current = self.redis_client.get(key)
            if current is None:
                self.redis_client.setex(key, 60, capacity - cost)
                return True
            
            current = int(current)
            if current >= cost:
                self.redis_client.decrby(key, cost)
                return True
            
            return False
        except Exception:
            # Fallback to allowing request if Redis fails
            return True
    
    async def get_remaining(self, key: str, tier: str = "free") -> Dict[str, int]:
        """Get remaining requests.
        
        Args:
            key: User ID or API key
            tier: Rate limit tier
            
        Returns:
            Dictionary with remaining requests per period
        """
        config = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        
        minute_key = f"{key}:minute"
        hour_key = f"{key}:hour"
        day_key = f"{key}:day"
        
        return {
            "minute": await self._get_bucket_remaining(minute_key),
            "hour": await self._get_bucket_remaining(hour_key),
            "day": await self._get_bucket_remaining(day_key),
        }
    
    async def _get_bucket_remaining(self, key: str) -> int:
        """Get remaining tokens in bucket.
        
        Args:
            key: Bucket key
            
        Returns:
            Remaining tokens
        """
        if self.storage == "memory":
            if key in self.buckets and "bucket" in self.buckets[key]:
                return await self.buckets[key]["bucket"].get_remaining()
            return 0
        
        elif self.storage == "redis":
            try:
                current = self.redis_client.get(key)
                return int(current) if current else 0
            except Exception:
                return 0
        
        return 0


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""
    pass


# Global rate limiter
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        storage = os.getenv("RATE_LIMIT_STORAGE", "memory")
        _rate_limiter = RateLimiter(storage)
    
    return _rate_limiter


def rate_limit(tier: str = "free", cost: int = 1):
    """Decorator for rate limiting.
    
    Args:
        tier: Rate limit tier
        cost: Cost in tokens
        
    Usage:
        @rate_limit(tier="pro", cost=1)
        async def my_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user key from kwargs or context
            user_id = kwargs.get("user_id", "anonymous")
            
            # Check rate limit
            limiter = get_rate_limiter()
            if not await limiter.check_rate_limit(user_id, tier, cost):
                raise RateLimitExceeded(f"Rate limit exceeded for tier: {tier}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
