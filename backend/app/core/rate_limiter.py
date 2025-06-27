import asyncio
import time
from typing import Dict
from dataclasses import dataclass
from asyncio import Lock


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    burst_limit: int = 10
    backoff_factor: float = 2.0
    max_retries: int = 3
    initial_delay: float = 1.0


class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, list] = {}
        self.locks: Dict[str, Lock] = {}
        self.retry_delays: Dict[str, float] = {}

    async def acquire(self, endpoint: str = "default") -> bool:
        if endpoint not in self.locks:
            self.locks[endpoint] = Lock()

        async with self.locks[endpoint]:
            current_time = time.time()

            if endpoint not in self.requests:
                self.requests[endpoint] = []

            # Clean old requests (older than 1 minute)
            minute_ago = current_time - 60
            self.requests[endpoint] = [
                req_time
                for req_time in self.requests[endpoint]
                if req_time > minute_ago
            ]

            # Check rate limits
            if len(self.requests[endpoint]) >= self.config.requests_per_minute:
                return False

            # Check burst limit (requests in last 10 seconds)
            ten_seconds_ago = current_time - 10
            recent_requests = [
                req_time
                for req_time in self.requests[endpoint]
                if req_time > ten_seconds_ago
            ]

            if len(recent_requests) >= self.config.burst_limit:
                return False

            # Record this request
            self.requests[endpoint].append(current_time)
            return True

    async def wait_if_needed(self, endpoint: str = "default") -> None:
        while not await self.acquire(endpoint):
            # Calculate delay based on current rate limit status
            current_time = time.time()
            minute_ago = current_time - 60

            if endpoint in self.requests:
                recent_requests = [
                    req_time
                    for req_time in self.requests[endpoint]
                    if req_time > minute_ago
                ]

                if recent_requests:
                    # Wait until the oldest request expires
                    oldest_request = min(recent_requests)
                    wait_time = max(0, oldest_request + 60 - current_time + 1)
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)

    async def exponential_backoff(self, endpoint: str, attempt: int) -> None:
        if endpoint not in self.retry_delays:
            self.retry_delays[endpoint] = self.config.initial_delay

        delay = self.retry_delays[endpoint] * (self.config.backoff_factor**attempt)
        delay = min(delay, 300)  # Max 5 minutes

        await asyncio.sleep(delay)
        self.retry_delays[endpoint] = delay

    def reset_endpoint(self, endpoint: str) -> None:
        if endpoint in self.requests:
            self.requests[endpoint] = []
        if endpoint in self.retry_delays:
            self.retry_delays[endpoint] = self.config.initial_delay

    def get_status(self, endpoint: str = "default") -> Dict:
        current_time = time.time()
        minute_ago = current_time - 60

        if endpoint not in self.requests:
            return {
                "requests_last_minute": 0,
                "remaining_requests": self.config.requests_per_minute,
                "reset_time": None,
            }

        recent_requests = [
            req_time for req_time in self.requests[endpoint] if req_time > minute_ago
        ]

        oldest_request = min(recent_requests) if recent_requests else None
        reset_time = oldest_request + 60 if oldest_request else None

        return {
            "requests_last_minute": len(recent_requests),
            "remaining_requests": max(
                0, self.config.requests_per_minute - len(recent_requests)
            ),
            "reset_time": reset_time,
            "current_delay": self.retry_delays.get(endpoint, self.config.initial_delay),
        }
