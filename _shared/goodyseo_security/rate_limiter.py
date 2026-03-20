"""
Sliding-window rate limiter — in-memory with optional Redis backend.
Adapted from ai-real-estate-assistant (MIT).

Per-client limits are keyed by SHA-256(api_key)[:12] to avoid storing raw keys.
"""

import hashlib
import logging
import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Optional, Tuple

logger = logging.getLogger("goodyseo.rate_limiter")

RateLimitResult = Tuple[bool, int, int, int]  # (allowed, limit, remaining, reset_s)


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter backed by in-process deques."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self._max = max(1, max_requests)
        self._window = max(1, window_seconds)
        self._lock = Lock()
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def configure(self, max_requests: int, window_seconds: int) -> None:
        with self._lock:
            self._max = max(1, max_requests)
            self._window = max(1, window_seconds)

    def check(self, key: str, now: Optional[float] = None) -> RateLimitResult:
        ts = time.time() if now is None else now
        key = key or "anonymous"
        with self._lock:
            q = self._events[key]
            cutoff = ts - self._window
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= self._max:
                reset_in = max(1, int((q[0] + self._window) - ts))
                return False, self._max, 0, reset_in
            q.append(ts)
            remaining = self._max - len(q)
            reset_in = max(1, int((q[0] + self._window) - ts)) if q else self._window
            return True, self._max, remaining, reset_in


class RedisRateLimiter:
    """Distributed rate limiter backed by Redis sorted sets. Falls back to in-memory."""

    def __init__(self, redis_url: str, max_requests: int = 60,
                 window_seconds: int = 60) -> None:
        self._max = max(1, max_requests)
        self._window = max(1, window_seconds)
        self._fallback = InMemoryRateLimiter(max_requests, window_seconds)
        self._redis = None
        try:
            import redis  # type: ignore[import]
            client = redis.from_url(redis_url, decode_responses=True,
                                    socket_timeout=2, socket_connect_timeout=2)
            client.ping()
            self._redis = client
            logger.info("Redis rate limiter connected: %s", redis_url)
        except Exception as e:
            logger.warning("Redis unavailable (%s) — using in-memory fallback.", e)

    def configure(self, max_requests: int, window_seconds: int) -> None:
        self._max = max(1, max_requests)
        self._window = max(1, window_seconds)
        self._fallback.configure(max_requests, window_seconds)

    def check(self, key: str, now: Optional[float] = None) -> RateLimitResult:
        if self._redis is None:
            return self._fallback.check(key, now)
        ts = time.time() if now is None else now
        rk = f"rl:{key}"
        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(rk, 0, ts - self._window)
            pipe.zcard(rk)
            pipe.zadd(rk, {str(ts): ts})
            pipe.expire(rk, self._window + 10)
            results = pipe.execute()
            count = results[1]
            if count >= self._max:
                oldest = self._redis.zrange(rk, 0, 0, withscores=True)
                reset_in = max(1, int((float(oldest[0][1]) + self._window) - ts)) if oldest else self._window
                return False, self._max, 0, reset_in
            oldest = self._redis.zrange(rk, 0, 0, withscores=True)
            reset_in = max(1, int((float(oldest[0][1]) + self._window) - ts)) if oldest else self._window
            return True, self._max, self._max - count, reset_in
        except Exception as e:
            logger.warning("Redis check failed (%s) — falling back.", e)
            return self._fallback.check(key, now)


def client_key(api_key: Optional[str]) -> str:
    """Hash an API key to a short, safe client identifier."""
    if not api_key:
        return "anonymous"
    return hashlib.sha256(api_key.encode()).hexdigest()[:12]


def build_rate_limiter(max_requests: Optional[int] = None,
                       window_seconds: int = 60) -> InMemoryRateLimiter | RedisRateLimiter:
    """Build rate limiter — uses Redis if REDIS_URL env var is set."""
    rpm = max_requests or int(os.getenv("RATE_LIMIT_RPM", "60"))
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        return RedisRateLimiter(redis_url, rpm, window_seconds)
    return InMemoryRateLimiter(rpm, window_seconds)
