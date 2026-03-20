"""Tests for response cache module (TASK-017: Production Deployment Optimization)."""

import time
from unittest.mock import MagicMock

import pytest

from utils.response_cache import CacheConfig, CacheEntry, InMemoryCache, ResponseCache


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_is_expired(self):
        """Test that cache entry correctly identifies expiration."""
        entry = CacheEntry(data={"test": "data"}, status_code=200, ttl=1)
        assert not entry.is_expired()

        # Wait for entry to expire
        time.sleep(1.1)
        assert entry.is_expired()

    def test_cache_entry_is_stale(self):
        """Test that cache entry correctly identifies staleness."""
        entry = CacheEntry(data={"test": "data"}, status_code=200, ttl=1)
        assert not entry.is_stale()

        # Wait for entry to become stale (2x TTL)
        time.sleep(2.1)
        assert entry.is_stale()

    def test_cache_entry_age_seconds(self):
        """Test that cache entry correctly reports age."""
        entry = CacheEntry(data={"test": "data"}, status_code=200, ttl=100)
        age = entry.age_seconds()
        assert 0 <= age < 1  # Should be very recent

        time.sleep(0.5)
        age_after = entry.age_seconds()
        assert age_after > age


class TestInMemoryCache:
    """Tests for InMemoryCache."""

    def test_in_memory_cache_set_and_get(self):
        """Test basic set and get operations."""
        cache = InMemoryCache(max_size=10)
        entry = CacheEntry(data={"key": "value"}, status_code=200, ttl=60)

        cache.set("test_key", entry)
        retrieved = cache.get("test_key")

        assert retrieved is not None
        assert retrieved.data == {"key": "value"}
        assert retrieved.status_code == 200

    def test_in_memory_cache_get_expired_returns_none(self):
        """Test that expired entries return None."""
        cache = InMemoryCache(max_size=10)
        entry = CacheEntry(data={"key": "value"}, status_code=200, ttl=1)

        cache.set("test_key", entry)
        time.sleep(1.1)

        retrieved = cache.get("test_key")
        assert retrieved is None

    def test_in_memory_cache_delete(self):
        """Test delete operation."""
        cache = InMemoryCache(max_size=10)
        entry = CacheEntry(data={"key": "value"}, status_code=200, ttl=60)

        cache.set("test_key", entry)
        assert cache.get("test_key") is not None

        deleted = cache.delete("test_key")
        assert deleted is True
        assert cache.get("test_key") is None

    def test_in_memory_cache_delete_nonexistent(self):
        """Test deleting a non-existent key returns False."""
        cache = InMemoryCache(max_size=10)
        deleted = cache.delete("nonexistent_key")
        assert deleted is False

    def test_in_memory_cache_clear(self):
        """Test clear operation."""
        cache = InMemoryCache(max_size=10)
        entry = CacheEntry(data={"key": "value"}, status_code=200, ttl=60)

        cache.set("key1", entry)
        cache.set("key2", entry)
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_in_memory_cache_lru_eviction(self):
        """Test that old entries are evicted when cache is full."""
        cache = InMemoryCache(max_size=3)

        for i in range(5):
            entry = CacheEntry(data={"value": i}, status_code=200, ttl=60)
            cache.set(f"key{i}", entry)

        # Should only have 3 entries due to max size
        assert cache.size() == 3

        # Oldest entries should be evicted
        assert cache.get("key0") is None
        assert cache.get("key1") is None

        # Newest entries should exist
        assert cache.get("key4") is not None
        assert cache.get("key3") is not None


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_default_values(self):
        """Test that CacheConfig has correct default values."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl_seconds == 300
        assert config.prefix == "api_cache"
        assert config.max_memory_mb == 100
        assert config.include_headers is True
        assert config.stale_while_revalidate is False

    def test_custom_values(self):
        """Test CacheConfig with custom values."""
        config = CacheConfig(
            enabled=False,
            ttl_seconds=600,
            prefix="custom_cache",
            max_memory_mb=200,
            stale_while_revalidate=True,
        )
        assert config.enabled is False
        assert config.ttl_seconds == 600
        assert config.prefix == "custom_cache"
        assert config.max_memory_mb == 200
        assert config.stale_while_revalidate is True


class TestResponseCache:
    """Tests for ResponseCache."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request."""
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/test"
        request.query_params = {"param1": "value1"}
        request.headers = {"X-Request-ID": "test-123"}
        return request

    @pytest.mark.asyncio
    async def test_response_cache_disabled_returns_none(self, mock_request):
        """Test that disabled cache returns None."""
        config = CacheConfig(enabled=False)
        cache = ResponseCache(config=config, redis_url=None)

        result = await cache.get(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_response_cache_set_and_get(self, mock_request):
        """Test basic cache set and get operations."""
        config = CacheConfig(enabled=True, ttl_seconds=60)
        cache = ResponseCache(config=config, redis_url=None)

        # Set a cache entry
        await cache.set(
            mock_request,
            data={"result": "success"},
            status_code=200,
            headers={"X-Custom": "header"},
        )

        # Get the cached entry
        retrieved = await cache.get(mock_request)

        assert retrieved is not None
        assert retrieved.data == {"result": "success"}
        assert retrieved.status_code == 200
        assert retrieved.headers == {"X-Custom": "header"}

    @pytest.mark.asyncio
    async def test_response_cache_delete(self, mock_request):
        """Test cache deletion."""
        config = CacheConfig(enabled=True)
        cache = ResponseCache(config=config, redis_url=None)

        await cache.set(mock_request, data={"result": "success"}, status_code=200)
        retrieved_before = await cache.get(mock_request)
        assert retrieved_before is not None

        deleted = await cache.delete(mock_request)
        assert deleted is True

        retrieved_after = await cache.get(mock_request)
        assert retrieved_after is None

    @pytest.mark.asyncio
    async def test_response_cache_clear_all(self, mock_request):
        """Test clearing all cache entries."""
        config = CacheConfig(enabled=True)
        cache = ResponseCache(config=config, redis_url=None)

        await cache.set(mock_request, data={"result": "success"}, status_code=200)
        await cache.clear_all()

        retrieved = await cache.get(mock_request)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_response_cache_get_stats(self, mock_request):
        """Test getting cache statistics."""
        config = CacheConfig(enabled=True, ttl_seconds=120)
        cache = ResponseCache(config=config, redis_url=None)

        await cache.set(mock_request, data={"result": "success"}, status_code=200)

        stats = cache.get_stats()
        assert stats["enabled"] is True
        assert stats["backend"] == "memory"
        assert stats["ttl_seconds"] == 120
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_response_cache_invalidate_by_prefix(self, mock_request):
        """Test cache invalidation by path prefix."""
        config = CacheConfig(enabled=True)
        cache = ResponseCache(config=config, redis_url=None)

        await cache.set(mock_request, data={"result": "success"}, status_code=200)

        # Invalidate by prefix
        count = cache.invalidate_by_prefix("/api/v1")
        assert count == 1

        # Entry should be cleared
        retrieved = await cache.get(mock_request)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_response_cache_no_backend(self, mock_request):
        """Test that operations work correctly when no backend is available."""
        config = CacheConfig(enabled=False)
        cache = ResponseCache(config=config, redis_url=None)

        # All operations should be no-ops
        retrieved = await cache.get(mock_request)
        assert retrieved is None

        await cache.set(mock_request, data={"test": "data"}, status_code=200)  # Should not raise

        retrieved_after = await cache.get(mock_request)
        assert retrieved_after is None

    @pytest.mark.asyncio
    async def test_response_cache_uses_in_memory_when_redis_unavailable(self, mock_request):
        """Test that cache works correctly even with invalid Redis URL."""
        config = CacheConfig(enabled=True)
        # Use an invalid Redis URL - should fall back to in-memory cache
        cache = ResponseCache(config=config, redis_url="redis://nonexistent:9999")

        # Verify cache is functional
        await cache.set(mock_request, data={"test": "data"}, status_code=200)
        retrieved = await cache.get(mock_request)
        assert retrieved is not None
        assert retrieved.data == {"test": "data"}

        # Verify backend is either redis (if package is available but connection failed)
        # or memory (as fallback)
        stats = cache.get_stats()
        assert stats["backend"] in ["redis", "memory"]


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request."""
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/properties"
        request.query_params = {"city": "Krakow", "rooms": "2"}
        return request

    @pytest.mark.asyncio
    async def test_cache_key_with_body_hash(self, mock_request):
        """Test that body hash is included in cache key when provided."""
        config = CacheConfig(enabled=True, ttl_seconds=60)
        cache = ResponseCache(config=config, redis_url=None)

        # Set entry with body hash
        await cache.set(
            mock_request,
            data={"result": "with_hash"},
            status_code=200,
            body_hash="abc123",
        )

        # Should be retrievable with same body hash
        retrieved = await cache.get(mock_request, body_hash="abc123")
        assert retrieved is not None
        assert retrieved.data == {"result": "with_hash"}

        # Should NOT be retrievable with different body hash
        retrieved_different = await cache.get(mock_request, body_hash="xyz789")
        assert retrieved_different is None

    @pytest.mark.asyncio
    async def test_cache_key_without_body_hash(self, mock_request):
        """Test that cache key works without body hash."""
        config = CacheConfig(enabled=True, ttl_seconds=60)
        cache = ResponseCache(config=config, redis_url=None)

        await cache.set(mock_request, data={"result": "no_hash"}, status_code=200)

        # Should be retrievable without body hash
        retrieved = await cache.get(mock_request)
        assert retrieved is not None
        assert retrieved.data == {"result": "no_hash"}

    def test_hash_request_body_string(self):
        """Test hashing a string request body."""
        config = CacheConfig(enabled=True)
        cache = ResponseCache(config=config, redis_url=None)

        hash1 = cache._hash_request_body("test body")
        hash2 = cache._hash_request_body("test body")

        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_hash_request_body_bytes(self):
        """Test hashing a bytes request body."""
        config = CacheConfig(enabled=True)
        cache = ResponseCache(config=config, redis_url=None)

        body_bytes = b"test body"
        hash1 = cache._hash_request_body(body_bytes)
        hash2 = cache._hash_request_body(body_bytes)

        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16


class TestCachedResponseDecorator:
    """Tests for cached_response decorator."""

    @pytest.fixture
    def mock_app_with_cache(self):
        """Create a mock FastAPI app with cache in state."""
        app = MagicMock()
        config = CacheConfig(enabled=True, ttl_seconds=60)
        cache = ResponseCache(config=config, redis_url=None)
        app.state.response_cache = cache
        return app

    @pytest.fixture
    def mock_request(self, mock_app_with_cache):
        """Create a mock Request with app reference."""
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/test"
        request.query_params = {}
        request.app = mock_app_with_cache
        return request

    @pytest.mark.asyncio
    async def test_cached_response_decorator_miss_no_cache(self):
        """Test that decorator executes function when cache is not configured."""
        from utils.response_cache import cached_response

        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/test"
        request.query_params = {}
        request.app = MagicMock()  # No cache in app state

        call_count = 0

        @cached_response(ttl_seconds=60)
        async def test_endpoint(request):
            nonlocal call_count
            call_count += 1
            return {"data": f"call_{call_count}"}

        # Each call should execute function (no cache)
        result1 = await test_endpoint(request)
        assert call_count == 1
        assert result1 == {"data": "call_1"}

        result2 = await test_endpoint(request)
        assert call_count == 2
        assert result2 == {"data": "call_2"}

    @pytest.mark.asyncio
    async def test_cached_response_decorator_caches_dict_result(self, mock_request):
        """Test that decorator correctly caches dict results."""
        from utils.response_cache import cached_response

        @cached_response(ttl_seconds=60)
        async def test_endpoint(request):
            return {"key": "value", "number": 42}

        result = await test_endpoint(mock_request)
        assert result == {"key": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_cached_response_decorator_caches_non_dict_result(self, mock_request):
        """Test that decorator wraps non-dict results."""
        from utils.response_cache import cached_response

        @cached_response(ttl_seconds=60)
        async def test_endpoint(request):
            return "string_result"

        result = await test_endpoint(mock_request)
        assert result == "string_result"
