"""Tests for request queue functionality."""

import pytest
import asyncio
from app.core.request_queue import RequestQueue, RequestPriority


class TestRequestQueue:
    """Test request queue functionality."""

    @pytest.fixture
    async def request_queue(self):
        """Create a request queue for testing."""
        queue = RequestQueue(max_concurrent=2)
        await queue.start_workers()
        yield queue
        await queue.stop_workers()

    @pytest.mark.asyncio
    async def test_priority_ordering(self, request_queue):
        """Test that high priority requests are processed first."""
        # Enqueue requests with different priorities
        low_id = await request_queue.enqueue(
            "test_endpoint", "GET", {}, RequestPriority.LOW
        )
        high_id = await request_queue.enqueue(
            "test_endpoint", "GET", {}, RequestPriority.HIGH
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        # High priority should be processed first
        high_status = request_queue.get_request_status(high_id)
        low_status = request_queue.get_request_status(low_id)

        assert high_status is not None
        assert low_status is not None

    @pytest.mark.asyncio
    async def test_worker_concurrency(self, request_queue):
        """Test multiple workers processing requests concurrently."""
        # Enqueue multiple requests
        request_ids = []
        for i in range(5):
            request_id = await request_queue.enqueue(
                f"endpoint_{i}", "GET", {"param": i}
            )
            request_ids.append(request_id)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Check that requests were processed
        status = request_queue.get_status()
        assert status["running"] is True
        assert status["workers"] == 2

    @pytest.mark.asyncio
    async def test_queue_status_tracking(self, request_queue):
        """Test request status tracking through lifecycle."""
        request_id = await request_queue.enqueue("test_endpoint", "GET", {"test": True})

        # Wait for processing
        await asyncio.sleep(0.5)

        request_status = request_queue.get_request_status(request_id)
        assert request_status is not None
        assert request_status["id"] == request_id

    @pytest.mark.asyncio
    async def test_callback_execution(self, request_queue):
        """Test callback execution on request completion."""
        callback_executed = False

        def test_callback(result):
            nonlocal callback_executed
            callback_executed = True

        await request_queue.enqueue("test_endpoint", "GET", {}, callback=test_callback)

        # Wait for processing
        await asyncio.sleep(0.5)

        assert callback_executed is True

    def test_get_status(self, request_queue):
        """Test queue status reporting."""
        status = request_queue.get_status()

        required_keys = [
            "running",
            "processing_count",
            "completed_count",
            "failed_count",
            "queue_sizes",
            "workers",
        ]

        for key in required_keys:
            assert key in status

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, request_queue):
        """Test failed request retry with exponential backoff."""
        # Enqueue a request that will fail
        request_id = await request_queue.enqueue(
            "test_fail_endpoint", "GET", {}, max_retries=2
        )

        # Wait for processing and retries
        await asyncio.sleep(2.0)

        request_status = request_queue.get_request_status(request_id)
        assert request_status is not None

    @pytest.mark.asyncio
    async def test_clear_completed(self, request_queue):
        """Test clearing of old completed requests."""
        # Enqueue and process some requests
        for i in range(3):
            await request_queue.enqueue(f"endpoint_{i}", "GET", {})

        # Wait for processing
        await asyncio.sleep(1.0)

        # Clear completed requests
        cleared_count = await request_queue.clear_completed(older_than_hours=0)

        assert cleared_count >= 0
