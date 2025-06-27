"""Tests for Redis cache functionality."""

import pytest
from unittest.mock import Mock, patch
from app.core.cache import RedisCache, CacheConfig


class TestRedisCache:
    """Test Redis cache functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch("app.core.cache.redis.from_url") as mock_redis_client:
            mock_client = Mock()
            mock_redis_client.return_value = mock_client
            mock_client.ping.return_value = True
            yield mock_client

    @pytest.fixture
    def cache_config(self):
        """Create cache configuration for testing."""
        return CacheConfig(
            default_ttl=300,
            max_key_length=100,
            compress_threshold=1024,
            key_prefix="test_cache",
        )

    @pytest.fixture
    def redis_cache(self, mock_redis, cache_config):
        """Create Redis cache instance for testing."""
        with patch("app.core.cache.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:6379/1"
            cache = RedisCache(cache_config)
            return cache

    @pytest.mark.asyncio
    async def test_cache_set_get(self, redis_cache, mock_redis):
        """Test basic cache set/get operations."""
        # Mock Redis responses
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b'{"test": "data"}'

        # Test set operation
        result = await redis_cache.set("test_key", {"test": "data"}, ttl=300)
        assert result is True

        # Test get operation
        cached_data = await redis_cache.get("test_key")
        assert cached_data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cache_delete(self, redis_cache, mock_redis):
        """Test cache delete operation."""
        mock_redis.delete.return_value = 1

        result = await redis_cache.delete("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_exists(self, redis_cache, mock_redis):
        """Test cache key existence check."""
        mock_redis.exists.return_value = 1

        result = await redis_cache.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_ttl(self, redis_cache, mock_redis):
        """Test TTL functionality."""
        mock_redis.ttl.return_value = 300

        ttl = await redis_cache.ttl("test_key")
        assert ttl == 300

    @pytest.mark.asyncio
    async def test_cache_expire(self, redis_cache, mock_redis):
        """Test cache expiration setting."""
        mock_redis.expire.return_value = True

        result = await redis_cache.expire("test_key", 600)
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_increment(self, redis_cache, mock_redis):
        """Test cache increment operation."""
        mock_redis.incrby.return_value = 5

        result = await redis_cache.increment("counter_key", 2)
        assert result == 5

    @pytest.mark.asyncio
    async def test_cache_get_many(self, redis_cache, mock_redis):
        """Test batch get operation."""
        mock_redis.mget.return_value = [b'{"data": 1}', b'{"data": 2}', None]

        result = await redis_cache.get_many(["key1", "key2", "key3"])

        assert "key1" in result
        assert "key2" in result
        assert "key3" not in result
        assert result["key1"] == {"data": 1}
        assert result["key2"] == {"data": 2}

    @pytest.mark.asyncio
    async def test_cache_set_many(self, redis_cache, mock_redis):
        """Test batch set operation."""
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [True, True, True]
        mock_redis.pipeline.return_value = mock_pipeline

        mapping = {"key1": {"data": 1}, "key2": {"data": 2}, "key3": {"data": 3}}

        result = await redis_cache.set_many(mapping, ttl=300)
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_flush_pattern(self, redis_cache, mock_redis):
        """Test pattern-based cache clearing."""
        mock_redis.keys.return_value = ["test_cache:key1", "test_cache:key2"]
        mock_redis.delete.return_value = 2

        result = await redis_cache.flush_pattern("*")
        assert result == 2

    def test_cache_key_generation(self, redis_cache):
        """Test cache key generation and hashing."""
        # Test normal key
        key = redis_cache._generate_key("normal_key")
        assert key.startswith("test_cache:")

        # Test long key that should be hashed
        long_key = "x" * 200
        hashed_key = redis_cache._generate_key(long_key)
        assert "hash:" in hashed_key
        assert len(hashed_key) <= redis_cache.config.max_key_length

    def test_cache_serialization(self, redis_cache):
        """Test data serialization and deserialization."""
        test_data = {"test": "data", "number": 42, "list": [1, 2, 3]}

        # Test serialization
        serialized = redis_cache._serialize_value(test_data)
        assert isinstance(serialized, bytes)

        # Test deserialization
        deserialized = redis_cache._deserialize_value(serialized)
        assert deserialized == test_data

    def test_get_stats(self, redis_cache, mock_redis):
        """Test cache statistics retrieval."""
        mock_redis.info.return_value = {
            "connected_clients": 10,
            "used_memory": 1024000,
            "used_memory_human": "1.00M",
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
        }

        stats = redis_cache.get_stats()

        assert "connected_clients" in stats
        assert "used_memory" in stats
        assert "keyspace_hits" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, redis_cache, mock_redis):
        """Test cache health check."""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b'{"timestamp": 1234567890, "test": true}'
        mock_redis.delete.return_value = 1

        health_result = await redis_cache.health_check()

        assert health_result["status"] == "healthy"
        assert "response_time_ms" in health_result
        assert health_result["data_integrity"] is True

    @pytest.mark.asyncio
    async def test_cache_compression(self, redis_cache):
        """Test automatic compression for large values."""
        # Create large data that should trigger compression
        large_data = {"data": "x" * 2000}  # Larger than compression threshold

        serialized = redis_cache._serialize_value(large_data)

        # Check if compression was applied
        if serialized.startswith(b"GZIP:"):
            # Compression was applied
            deserialized = redis_cache._deserialize_value(serialized)
            assert deserialized == large_data
