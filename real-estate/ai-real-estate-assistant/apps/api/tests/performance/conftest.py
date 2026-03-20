"""Performance test configuration and fixtures."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    response_times: list[float] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    status_codes: dict[int, int] = field(default_factory=lambda: defaultdict(int))

    def add_response(self, response_time: float, status_code: int) -> None:
        """Add a response measurement."""
        self.response_times.append(response_time)
        self.status_codes[status_code] += 1

    def add_error(self, error: dict[str, Any]) -> None:
        """Add an error record."""
        self.errors.append(error)

    @property
    def total_requests(self) -> int:
        """Total number of requests made."""
        return len(self.response_times)

    @property
    def success_rate(self) -> float:
        """Calculate success rate (2xx and 3xx responses)."""
        if not self.response_times:
            return 0.0
        successful = sum(count for code, count in self.status_codes.items() if 200 <= code < 400)
        return successful / len(self.response_times) * 100

    def percentile(self, p: float) -> float:
        """Calculate the p-th percentile of response times."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * p / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def p50(self) -> float:
        """Median response time."""
        return self.percentile(50)

    @property
    def p95(self) -> float:
        """95th percentile response time."""
        return self.percentile(95)

    @property
    def p99(self) -> float:
        """99th percentile response time."""
        return self.percentile(99)

    @property
    def avg(self) -> float:
        """Average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def min(self) -> float:
        """Minimum response time."""
        return min(self.response_times) if self.response_times else 0.0

    @property
    def max(self) -> float:
        """Maximum response time."""
        return max(self.response_times) if self.response_times else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "success_rate": f"{self.success_rate:.2f}%",
            "response_times": {
                "min": f"{self.min:.3f}s",
                "avg": f"{self.avg:.3f}s",
                "p50": f"{self.p50:.3f}s",
                "p95": f"{self.p95:.3f}s",
                "p99": f"{self.p99:.3f}s",
                "max": f"{self.max:.3f}s",
            },
            "status_codes": dict(self.status_codes),
            "errors": self.errors,
        }


@pytest.fixture
def metrics() -> PerformanceMetrics:
    """Create a fresh metrics container."""
    return PerformanceMetrics()


@pytest.fixture
def performance_thresholds() -> dict[str, dict[str, float]]:
    """Performance thresholds for different endpoints."""
    return {
        "search": {
            "p95_max": 2.0,  # 2 seconds
            "avg_max": 1.0,  # 1 second
            "success_rate_min": 99.0,  # 99%
        },
        "chat": {
            "p95_max": 8.0,  # 8 seconds (LLM processing)
            "avg_max": 5.0,  # 5 seconds
            "success_rate_min": 95.0,  # 95%
        },
        "documents": {
            "p95_max": 5.0,  # 5 seconds for 10MB
            "avg_max": 2.0,  # 2 seconds
            "success_rate_min": 99.0,  # 99%
        },
        "health": {
            "p95_max": 0.1,  # 100ms
            "avg_max": 0.05,  # 50ms
            "success_rate_min": 100.0,  # 100%
        },
        "leads": {
            "p95_max": 1.0,  # 1 second
            "avg_max": 0.5,  # 500ms
            "success_rate_min": 99.0,  # 99%
        },
    }


@pytest_asyncio.fixture
async def perf_client():
    """Create an async HTTP client for performance testing."""
    async with AsyncClient(
        base_url="http://localhost:8000",
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authed_perf_client(perf_client: AsyncClient, api_key: str):
    """Create an authenticated async HTTP client for performance testing."""
    perf_client.headers["X-API-Key"] = api_key
    yield perf_client


@pytest.fixture
def api_key() -> str:
    """Get API key for testing."""
    import os

    return os.environ.get("API_ACCESS_KEY", "test-api-key")


async def measure_request(
    client: AsyncClient,
    method: str,
    url: str,
    metrics: PerformanceMetrics,
    **kwargs: Any,
) -> tuple[float, int]:
    """Measure a single HTTP request and record metrics."""
    start_time = time.perf_counter()
    try:
        response = await getattr(client, method.lower())(url, **kwargs)
        elapsed = time.perf_counter() - start_time
        metrics.add_response(elapsed, response.status_code)
        return elapsed, response.status_code
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        metrics.add_error(
            {
                "url": url,
                "method": method,
                "error": str(e),
                "elapsed": elapsed,
            }
        )
        metrics.add_response(elapsed, 0)
        raise


async def concurrent_requests(
    client: AsyncClient,
    method: str,
    url: str,
    num_requests: int,
    metrics: PerformanceMetrics,
    **kwargs: Any,
) -> list[tuple[float, int]]:
    """Execute concurrent requests and collect metrics."""
    tasks = [measure_request(client, method, url, metrics, **kwargs) for _ in range(num_requests)]
    return await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
def benchmark_results() -> dict[str, Any]:
    """Container for benchmark results."""
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": {},
        "passed": True,
        "failures": [],
    }
