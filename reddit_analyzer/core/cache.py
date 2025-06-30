import json
import time
import hashlib
from typing import Any, Dict, Optional
from dataclasses import dataclass
import redis
from reddit_analyzer.config import get_settings


@dataclass
class CacheConfig:
    default_ttl: int = 3600  # 1 hour
    max_key_length: int = 250
    compress_threshold: int = 1024  # Compress values larger than 1KB
    key_prefix: str = "reddit_analyzer"


class RedisCache:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        settings = get_settings()

        # Parse Redis URL
        redis_url = settings.redis_url
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False,  # We'll handle encoding ourselves
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # Test connection
        try:
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _generate_key(self, key: str) -> str:
        full_key = f"{self.config.key_prefix}:{key}"

        # Hash long keys to avoid Redis key length limits
        if len(full_key) > self.config.max_key_length:
            key_hash = hashlib.sha256(full_key.encode()).hexdigest()
            full_key = f"{self.config.key_prefix}:hash:{key_hash}"

        return full_key

    def _serialize_value(self, value: Any) -> bytes:
        serialized = json.dumps(value, default=str).encode("utf-8")

        # Optionally compress large values
        if len(serialized) > self.config.compress_threshold:
            import gzip

            compressed = gzip.compress(serialized)
            # Only use compression if it actually reduces size
            if len(compressed) < len(serialized):
                return b"GZIP:" + compressed

        return serialized

    def _deserialize_value(self, value: bytes) -> Any:
        if value.startswith(b"GZIP:"):
            import gzip

            decompressed = gzip.decompress(value[5:])
            return json.loads(decompressed.decode("utf-8"))

        return json.loads(value.decode("utf-8"))

    async def get(self, key: str) -> Optional[Any]:
        try:
            redis_key = self._generate_key(key)
            value = self.redis_client.get(redis_key)

            if value is None:
                return None

            return self._deserialize_value(value)

        except (redis.RedisError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        try:
            redis_key = self._generate_key(key)
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.config.default_ttl

            result = self.redis_client.set(
                redis_key, serialized_value, ex=ttl, nx=nx, xx=xx
            )

            return bool(result)

        except (redis.RedisError, json.JSONEncodeError) as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            redis_key = self._generate_key(key)
            result = self.redis_client.delete(redis_key)
            return result > 0

        except redis.RedisError as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            redis_key = self._generate_key(key)
            return bool(self.redis_client.exists(redis_key))

        except redis.RedisError as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        try:
            redis_key = self._generate_key(key)
            return self.redis_client.ttl(redis_key)

        except redis.RedisError as e:
            print(f"Cache TTL error for key {key}: {e}")
            return -1

    async def expire(self, key: str, ttl: int) -> bool:
        try:
            redis_key = self._generate_key(key)
            return bool(self.redis_client.expire(redis_key, ttl))

        except redis.RedisError as e:
            print(f"Cache expire error for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        try:
            redis_key = self._generate_key(key)
            return self.redis_client.incrby(redis_key, amount)

        except redis.RedisError as e:
            print(f"Cache increment error for key {key}: {e}")
            return None

    async def get_many(self, keys: list) -> Dict[str, Any]:
        try:
            redis_keys = [self._generate_key(key) for key in keys]
            values = self.redis_client.mget(redis_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = self._deserialize_value(value)
                    except Exception as e:
                        print(f"Failed to deserialize value for key {key}: {e}")

            return result

        except redis.RedisError as e:
            print(f"Cache get_many error: {e}")
            return {}

    async def set_many(
        self, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        try:
            ttl = ttl or self.config.default_ttl
            pipe = self.redis_client.pipeline()

            for key, value in mapping.items():
                redis_key = self._generate_key(key)
                serialized_value = self._serialize_value(value)
                pipe.set(redis_key, serialized_value, ex=ttl)

            results = pipe.execute()
            return all(results)

        except (redis.RedisError, json.JSONEncodeError) as e:
            print(f"Cache set_many error: {e}")
            return False

    async def flush_pattern(self, pattern: str) -> int:
        try:
            full_pattern = self._generate_key(pattern)
            keys = self.redis_client.keys(full_pattern)

            if keys:
                return self.redis_client.delete(*keys)

            return 0

        except redis.RedisError as e:
            print(f"Cache flush_pattern error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace": info.get("db0", {}),
            }

        except redis.RedisError as e:
            print(f"Cache stats error: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        try:
            start_time = time.time()

            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            test_value = {"timestamp": time.time(), "test": True}

            # Set operation
            await self.set(test_key, test_value, ttl=60)

            # Get operation
            retrieved_value = await self.get(test_key)

            # Delete operation
            await self.delete(test_key)

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "operations_tested": ["set", "get", "delete"],
                "data_integrity": retrieved_value == test_value,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "response_time_ms": None}

    def close(self):
        try:
            self.redis_client.close()
        except Exception as e:
            print(f"Error closing Redis connection: {e}")


# Global cache instance
_cache_instance = None


def get_cache() -> RedisCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
