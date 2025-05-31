"""
Tests for the cache service.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache_service import CacheService, get_cache_service


class TestCacheService:
    """Test the Redis cache service."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        return CacheService("redis://localhost:6379")

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_connect_success(self, cache_service):
        """Test successful Redis connection."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            mock_client.ping.return_value = True

            result = await cache_service.connect()

            assert result is True
            assert cache_service._is_connected is True
            mock_from_url.assert_called_once_with(
                "redis://localhost:6379", decode_responses=True
            )
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, cache_service):
        """Test Redis connection failure."""
        from redis.exceptions import RedisError

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            mock_client.ping.side_effect = RedisError("Connection failed")

            result = await cache_service.connect()

            assert result is False
            assert cache_service._is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, cache_service):
        """Test Redis disconnection."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True

        await cache_service.disconnect()

        mock_client.close.assert_called_once()
        assert cache_service._is_connected is False

    @pytest.mark.asyncio
    async def test_set_value_success(self, cache_service):
        """Test setting a value in cache."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.set("test_key", {"data": "value"}, ttl=300)

            assert result is True
            mock_client.setex.assert_called_once_with(
                "test_key", 300, json.dumps({"data": "value"}, default=str)
            )

    @pytest.mark.asyncio
    async def test_set_value_without_ttl(self, cache_service):
        """Test setting a value without TTL."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.set("test_key", {"data": "value"})

            assert result is True
            mock_client.set.assert_called_once_with(
                "test_key", json.dumps({"data": "value"}, default=str)
            )

    @pytest.mark.asyncio
    async def test_set_value_with_namespace(self, cache_service):
        """Test setting a value with namespace."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.set(
                "test_key", {"data": "value"}, namespace="metrics"
            )

            assert result is True
            mock_client.set.assert_called_once_with(
                "metrics:test_key", json.dumps({"data": "value"}, default=str)
            )

    @pytest.mark.asyncio
    async def test_get_value_success(self, cache_service):
        """Test getting a value from cache."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.get.return_value = json.dumps({"data": "value"})

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.get("test_key")

            assert result == {"data": "value"}
            mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_value_not_found(self, cache_service):
        """Test getting a non-existent value."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.get.return_value = None

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.get("test_key", default="default_value")

            assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_value_with_namespace(self, cache_service):
        """Test getting a value with namespace."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.get.return_value = json.dumps({"data": "value"})

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.get("test_key", namespace="metrics")

            assert result == {"data": "value"}
            mock_client.get.assert_called_once_with("metrics:test_key")

    @pytest.mark.asyncio
    async def test_delete_value(self, cache_service):
        """Test deleting a value from cache."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.delete.return_value = 1

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.delete("test_key")

            assert result is True
            mock_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_value(self, cache_service):
        """Test checking if a value exists."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.exists.return_value = 1

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.exists("test_key")

            assert result is True
            mock_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_expire_value(self, cache_service):
        """Test setting expiration for a value."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.expire.return_value = True

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.expire("test_key", 300)

            assert result is True
            mock_client.expire.assert_called_once_with("test_key", 300)

    @pytest.mark.asyncio
    async def test_clear_namespace(self, cache_service):
        """Test clearing all keys in a namespace."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.keys.return_value = ["metrics:key1", "metrics:key2"]
        mock_client.delete.return_value = 2

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.clear_namespace("metrics")

            assert result == 2
            mock_client.keys.assert_called_once_with("metrics:*")
            mock_client.delete.assert_called_once_with("metrics:key1", "metrics:key2")

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test getting cache statistics."""
        mock_client = AsyncMock()
        cache_service._redis_client = mock_client
        cache_service._is_connected = True
        mock_client.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024000,
            "used_memory_human": "1.02M",
            "keyspace_hits": 100,
            "keyspace_misses": 10,
            "total_commands_processed": 1000,
            "uptime_in_seconds": 3600,
        }

        with patch.object(cache_service, "_ensure_connection", return_value=True):
            result = await cache_service.get_stats()

            expected = {
                "connected_clients": 5,
                "used_memory": 1024000,
                "used_memory_human": "1.02M",
                "keyspace_hits": 100,
                "keyspace_misses": 10,
                "total_commands_processed": 1000,
                "uptime_in_seconds": 3600,
            }
            assert result == expected

    def test_build_key_without_namespace(self, cache_service):
        """Test building cache key without namespace."""
        result = cache_service._build_key("test_key")
        assert result == "test_key"

    def test_build_key_with_namespace(self, cache_service):
        """Test building cache key with namespace."""
        result = cache_service._build_key("test_key", "metrics")
        assert result == "metrics:test_key"

    @pytest.mark.asyncio
    async def test_ensure_connection_when_connected(self, cache_service):
        """Test ensure connection when already connected."""
        cache_service._is_connected = True

        with patch.object(cache_service, "is_connected", return_value=True):
            result = await cache_service._ensure_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_connection_when_disconnected(self, cache_service):
        """Test ensure connection when disconnected."""
        cache_service._is_connected = False

        with patch.object(cache_service, "connect", return_value=True):
            result = await cache_service._ensure_connection()
            assert result is True


class TestGlobalCacheService:
    """Test the global cache service functions."""

    @pytest.mark.asyncio
    async def test_get_cache_service(self):
        """Test getting global cache service instance."""
        with patch("app.services.cache_service._cache_service", None):
            with patch.object(
                CacheService, "connect", return_value=True
            ) as mock_connect:
                service = await get_cache_service()

                assert isinstance(service, CacheService)
                mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_service_existing_instance(self):
        """Test getting existing global cache service instance."""
        existing_service = CacheService()

        with patch("app.services.cache_service._cache_service", existing_service):
            service = await get_cache_service()

            assert service is existing_service
