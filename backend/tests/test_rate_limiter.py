"""Tests for rate limiting functionality."""

import pytest
import time
from app.core.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimiter:
    """Test rate limiter functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        config = RateLimitConfig(
            requests_per_minute=10,  # Low limit for testing
            burst_limit=3,
            backoff_factor=2.0,
            max_retries=3,
        )
        return RateLimiter(config)

    @pytest.mark.asyncio
    async def test_rate_limit_acquisition(self, rate_limiter):
        """Test rate limit token acquisition."""
        # Should be able to acquire tokens up to burst limit
        for i in range(3):
            result = await rate_limiter.acquire("test_endpoint")
            assert result is True

        # Should fail to acquire more tokens immediately
        result = await rate_limiter.acquire("test_endpoint")
        assert result is False

    @pytest.mark.asyncio
    async def test_burst_limit_protection(self, rate_limiter):
        """Test burst limit enforcement."""
        # Acquire up to burst limit
        for i in range(3):
            await rate_limiter.acquire("test_endpoint")

        # Next acquisition should fail
        result = await rate_limiter.acquire("test_endpoint")
        assert result is False

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, rate_limiter):
        """Test exponential backoff calculation."""
        start_time = time.time()
        await rate_limiter.exponential_backoff("test_endpoint", 1)
        elapsed = time.time() - start_time

        # Should wait for at least the base delay
        assert elapsed >= rate_limiter.config.initial_delay

    @pytest.mark.asyncio
    async def test_endpoint_isolation(self, rate_limiter):
        """Test that different endpoints have separate limits."""
        # Use up rate limit for endpoint1
        for i in range(3):
            await rate_limiter.acquire("endpoint1")

        # Should still be able to acquire for endpoint2
        result = await rate_limiter.acquire("endpoint2")
        assert result is True

    def test_rate_limit_reset(self, rate_limiter):
        """Test rate limit reset functionality."""
        # Set some requests for an endpoint
        rate_limiter.requests["test_endpoint"] = [time.time()]

        # Reset the endpoint
        rate_limiter.reset_endpoint("test_endpoint")

        # Should have no requests recorded
        assert rate_limiter.requests["test_endpoint"] == []

    def test_get_status(self, rate_limiter):
        """Test rate limiter status reporting."""
        status = rate_limiter.get_status("test_endpoint")

        assert "requests_last_minute" in status
        assert "remaining_requests" in status
        assert "reset_time" in status
        assert status["remaining_requests"] == rate_limiter.config.requests_per_minute

    @pytest.mark.asyncio
    async def test_wait_if_needed(self, rate_limiter):
        """Test wait functionality."""
        # Use up the rate limit
        for i in range(3):
            await rate_limiter.acquire("test_endpoint")

        # This should wait and then succeed
        start_time = time.time()
        await rate_limiter.wait_if_needed("test_endpoint")
        elapsed = time.time() - start_time

        # Should have waited some time
        assert elapsed > 0
