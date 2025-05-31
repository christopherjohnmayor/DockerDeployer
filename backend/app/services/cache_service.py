"""
Cache service for Redis-based caching with configurable TTL.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with TTL support."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379", decode_responses: bool = True
    ):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL
            decode_responses: Whether to decode responses as strings
        """
        self.redis_url = redis_url
        self.decode_responses = decode_responses
        self._redis_client: Optional[redis.Redis] = None
        self._is_connected = False

    async def connect(self) -> bool:
        """
        Connect to Redis server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._redis_client = redis.from_url(
                self.redis_url, decode_responses=self.decode_responses
            )
            await self._redis_client.ping()
            self._is_connected = True
            logger.info("Connected to Redis cache service")
            return True
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis server."""
        if self._redis_client:
            await self._redis_client.close()
            self._is_connected = False
            logger.info("Disconnected from Redis cache service")

    async def is_connected(self) -> bool:
        """
        Check if Redis connection is active.

        Returns:
            True if connected, False otherwise
        """
        if not self._redis_client:
            return False

        try:
            await self._redis_client.ping()
            return True
        except RedisError:
            self._is_connected = False
            return False

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> bool:
        """
        Set a value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            namespace: Optional namespace prefix

        Returns:
            True if successful, False otherwise
        """
        if not await self._ensure_connection():
            return False

        try:
            cache_key = self._build_key(key, namespace)
            serialized_value = json.dumps(value, default=str)

            if ttl:
                await self._redis_client.setex(cache_key, ttl, serialized_value)
            else:
                await self._redis_client.set(cache_key, serialized_value)

            logger.debug(f"Cached value for key: {cache_key}")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def get(
        self, key: str, namespace: Optional[str] = None, default: Any = None
    ) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key
            namespace: Optional namespace prefix
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not await self._ensure_connection():
            return default

        try:
            cache_key = self._build_key(key, namespace)
            value = await self._redis_client.get(cache_key)

            if value is None:
                return default

            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default

    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key
            namespace: Optional namespace prefix

        Returns:
            True if successful, False otherwise
        """
        if not await self._ensure_connection():
            return False

        try:
            cache_key = self._build_key(key, namespace)
            result = await self._redis_client.delete(cache_key)
            logger.debug(f"Deleted cache key: {cache_key}")
            return result > 0
        except RedisError as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key
            namespace: Optional namespace prefix

        Returns:
            True if key exists, False otherwise
        """
        if not await self._ensure_connection():
            return False

        try:
            cache_key = self._build_key(key, namespace)
            return await self._redis_client.exists(cache_key) > 0
        except RedisError as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int, namespace: Optional[str] = None) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds
            namespace: Optional namespace prefix

        Returns:
            True if successful, False otherwise
        """
        if not await self._ensure_connection():
            return False

        try:
            cache_key = self._build_key(key, namespace)
            return await self._redis_client.expire(cache_key, ttl)
        except RedisError as e:
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all keys in a namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            Number of keys deleted
        """
        if not await self._ensure_connection():
            return 0

        try:
            pattern = f"{namespace}:*"
            keys = await self._redis_client.keys(pattern)

            if keys:
                deleted = await self._redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys from namespace: {namespace}")
                return deleted

            return 0
        except RedisError as e:
            logger.error(f"Error clearing namespace {namespace}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not await self._ensure_connection():
            return {}

        try:
            info = await self._redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except RedisError as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    def _build_key(self, key: str, namespace: Optional[str] = None) -> str:
        """
        Build cache key with optional namespace.

        Args:
            key: Base key
            namespace: Optional namespace prefix

        Returns:
            Full cache key
        """
        if namespace:
            return f"{namespace}:{key}"
        return key

    async def _ensure_connection(self) -> bool:
        """
        Ensure Redis connection is active.

        Returns:
            True if connected, False otherwise
        """
        if not self._is_connected:
            return await self.connect()

        if not await self.is_connected():
            return await self.connect()

        return True


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    return _cache_service


async def close_cache_service():
    """Close the global cache service instance."""
    global _cache_service
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None
