import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import uuid4


class RequestPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueuedRequest:
    id: str
    endpoint: str
    method: str
    params: Dict[str, Any]
    priority: RequestPriority
    status: RequestStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempts: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    callback: Optional[str] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        return data


class RequestQueue:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queues: Dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }
        self.processing: Dict[str, QueuedRequest] = {}
        self.completed: List[QueuedRequest] = []
        self.failed: List[QueuedRequest] = []
        self.callbacks: Dict[str, Callable] = {}
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False

    async def enqueue(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        priority: RequestPriority = RequestPriority.MEDIUM,
        max_retries: int = 3,
        callback: Optional[Callable] = None,
    ) -> str:
        request_id = str(uuid4())

        request = QueuedRequest(
            id=request_id,
            endpoint=endpoint,
            method=method,
            params=params,
            priority=priority,
            status=RequestStatus.PENDING,
            created_at=time.time(),
            max_retries=max_retries,
        )

        if callback:
            callback_name = f"callback_{request_id}"
            self.callbacks[callback_name] = callback
            request.callback = callback_name

        await self.queues[priority].put(request)
        return request_id

    async def start_workers(self) -> None:
        if self._running:
            return

        self._running = True
        self._worker_tasks = [
            asyncio.create_task(self._worker(f"worker_{i}"))
            for i in range(self.max_concurrent)
        ]

    async def stop_workers(self) -> None:
        self._running = False

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks = []

    async def _worker(self, worker_name: str) -> None:
        while self._running:
            try:
                request = await self._get_next_request()
                if request is None:
                    await asyncio.sleep(0.1)
                    continue

                await self._process_request(request, worker_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)

    async def _get_next_request(self) -> Optional[QueuedRequest]:
        # Process requests by priority (highest first)
        for priority in sorted(RequestPriority, key=lambda x: x.value, reverse=True):
            try:
                request = self.queues[priority].get_nowait()
                self.processing[request.id] = request
                request.status = RequestStatus.PROCESSING
                request.started_at = time.time()
                return request
            except asyncio.QueueEmpty:
                continue

        return None

    async def _process_request(self, request: QueuedRequest, worker_name: str) -> None:
        try:
            request.attempts += 1

            # Simulate request processing
            # In real implementation, this would call the actual Reddit API
            result = await self._execute_request(request)

            # Mark as completed
            request.status = RequestStatus.COMPLETED
            request.completed_at = time.time()

            # Execute callback if present
            if request.callback and request.callback in self.callbacks:
                try:
                    await self.callbacks[request.callback](result)
                except Exception as callback_error:
                    print(f"Callback error for {request.id}: {callback_error}")

            # Move to completed
            self.completed.append(request)

        except Exception as e:
            await self._handle_request_error(request, str(e))

        finally:
            # Remove from processing
            if request.id in self.processing:
                del self.processing[request.id]

    async def _execute_request(self, request: QueuedRequest) -> Dict[str, Any]:
        # Simulate API call delay
        await asyncio.sleep(0.1)

        # Simulate occasional failures for testing
        if request.attempts == 1 and request.endpoint.startswith("test_fail"):
            raise Exception("Simulated API error")

        return {
            "request_id": request.id,
            "endpoint": request.endpoint,
            "method": request.method,
            "params": request.params,
            "result": "success",
            "timestamp": time.time(),
        }

    async def _handle_request_error(
        self, request: QueuedRequest, error_message: str
    ) -> None:
        request.error_message = error_message

        if request.attempts < request.max_retries:
            # Retry the request
            request.status = RequestStatus.RETRYING
            await asyncio.sleep(2**request.attempts)  # Exponential backoff
            await self.queues[request.priority].put(request)
        else:
            # Mark as failed
            request.status = RequestStatus.FAILED
            request.completed_at = time.time()
            self.failed.append(request)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "processing_count": len(self.processing),
            "completed_count": len(self.completed),
            "failed_count": len(self.failed),
            "queue_sizes": {
                priority.name: self.queues[priority].qsize()
                for priority in RequestPriority
            },
            "workers": len(self._worker_tasks),
        }

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        # Check processing
        if request_id in self.processing:
            return self.processing[request_id].to_dict()

        # Check completed
        for request in self.completed:
            if request.id == request_id:
                return request.to_dict()

        # Check failed
        for request in self.failed:
            if request.id == request_id:
                return request.to_dict()

        return None

    async def clear_completed(self, older_than_hours: int = 24) -> int:
        cutoff_time = time.time() - (older_than_hours * 3600)

        old_completed = [
            req
            for req in self.completed
            if req.completed_at and req.completed_at < cutoff_time
        ]

        old_failed = [
            req
            for req in self.failed
            if req.completed_at and req.completed_at < cutoff_time
        ]

        self.completed = [
            req
            for req in self.completed
            if not (req.completed_at and req.completed_at < cutoff_time)
        ]

        self.failed = [
            req
            for req in self.failed
            if not (req.completed_at and req.completed_at < cutoff_time)
        ]

        # Clean up old callbacks
        old_callbacks = []
        for callback_name in list(self.callbacks.keys()):
            if any(req.callback == callback_name for req in old_completed + old_failed):
                old_callbacks.append(callback_name)

        for callback_name in old_callbacks:
            del self.callbacks[callback_name]

        return len(old_completed) + len(old_failed)
