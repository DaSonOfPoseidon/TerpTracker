"""
Redis-based caching and rate limiting service.
"""

import json
import redis.asyncio as redis
from typing import Optional, Any
from datetime import timedelta
from app.core.config import settings

class CacheService:
    """Redis cache service for storing analysis results and rate limiting."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis = None

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int = 900):
        """
        Set a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 15 minutes)
        """
        if not self.redis:
            return

        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Cache set error: {e}")

    async def delete(self, key: str):
        """Delete a key from cache."""
        if not self.redis:
            return

        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")

    async def check_rate_limit(self, client_id: str, limit: int = 30, window: int = 60) -> tuple[bool, int]:
        """
        Check if a client has exceeded rate limit.

        Args:
            client_id: Unique client identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if not self.redis:
            return True, limit  # Allow if Redis unavailable

        try:
            key = f"rate_limit:{client_id}"
            current = await self.redis.get(key)

            if current is None:
                # First request in window
                await self.redis.setex(key, window, "1")
                return True, limit - 1
            else:
                count = int(current)
                if count >= limit:
                    return False, 0
                else:
                    await self.redis.incr(key)
                    return True, limit - count - 1

        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True, limit  # Allow on error

# Global cache instance
cache_service = CacheService()
