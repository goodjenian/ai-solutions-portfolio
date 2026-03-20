"""Load Testing Scenarios.

Tests system behavior under sustained load:
- 100 concurrent users
- 10 minutes sustained load
- Various endpoint mixes
"""

import asyncio
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import AsyncClient

from tests.performance.conftest import (
    PerformanceMetrics,
    measure_request,
)


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    concurrent_users: int = 100
    duration_seconds: int = 60  # Reduced for CI, increase for real testing
    ramp_up_seconds: int = 10
    think_time_min: float = 0.5
    think_time_max: float = 2.0
    timeout: float = 30.0


@dataclass
class UserSession:
    """Simulates a user session."""

    user_id: int
    requests_made: int = 0
    errors: list[dict[str, Any]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class LoadTestScenario:
    """Base class for load test scenarios."""

    def __init__(self, client: AsyncClient, config: LoadTestConfig):
        self.client = client
        self.config = config
        self.metrics = PerformanceMetrics()
        self.sessions: list[UserSession] = []

    async def think_time(self) -> None:
        """Simulate user think time between requests."""
        delay = random.uniform(self.config.think_time_min, self.config.think_time_max)
        await asyncio.sleep(delay)

    async def user_workflow(self, user_id: int, stop_event: asyncio.Event) -> None:
        """Override in subclasses to define user behavior."""
        raise NotImplementedError

    async def run(self) -> PerformanceMetrics:
        """Run the load test."""
        stop_event = asyncio.Event()
        _start_time = time.time()

        # Set up stop timer
        async def stop_after_duration():
            await asyncio.sleep(self.config.duration_seconds)
            stop_event.set()

        # Create user tasks with ramp-up
        user_tasks = []

        async def ramp_up_users():
            users_per_batch = max(1, self.config.concurrent_users // self.config.ramp_up_seconds)
            for i in range(self.config.concurrent_users):
                session = UserSession(user_id=i)
                self.sessions.append(session)
                task = asyncio.create_task(self.user_workflow(i, stop_event))
                user_tasks.append(task)

                if (i + 1) % users_per_batch == 0:
                    await asyncio.sleep(1)  # Ramp up delay

        # Run the test
        stop_task = asyncio.create_task(stop_after_duration())
        await ramp_up_users()

        # Wait for completion
        await stop_task
        stop_event.set()

        # Wait for all users to finish current request
        await asyncio.gather(*user_tasks, return_exceptions=True)

        return self.metrics


class HealthCheckScenario(LoadTestScenario):
    """Simple health check load test."""

    async def user_workflow(self, user_id: int, stop_event: asyncio.Event) -> None:
        """Repeated health checks."""
        while not stop_event.is_set():
            try:
                await measure_request(self.client, "GET", "/health", self.metrics)
            except Exception as e:
                self.sessions[user_id].errors.append({"error": str(e), "time": time.time()})
            await self.think_time()


class MixedEndpointScenario(LoadTestScenario):
    """Mixed endpoint load test simulating realistic usage."""

    ENDPOINT_WEIGHTS = [
        ("/health", "GET", None, 0.1),
        ("/api/v1/properties", "GET", None, 0.3),
        ("/api/v1/properties/search", "POST", {"query": "apartments", "limit": 10}, 0.2),
        ("/api/v1/leads", "GET", None, 0.15),
        ("/api/v1/documents", "GET", None, 0.1),
        ("/api/v1/chat", "POST", {"message": "Hello", "session_id": "load"}, 0.15),
    ]

    async def user_workflow(self, user_id: int, stop_event: asyncio.Event) -> None:
        """Mixed endpoint requests."""
        while not stop_event.is_set():
            try:
                # Weighted random endpoint selection
                r = random.random()
                cumulative = 0.0
                endpoint, method, body = None, None, None

                for ep, m, b, weight in self.ENDPOINT_WEIGHTS:
                    cumulative += weight
                    if r <= cumulative:
                        endpoint, method, body = ep, m, b
                        break

                if endpoint:
                    kwargs = {}
                    if body:
                        kwargs["json"] = body

                    await measure_request(self.client, method, endpoint, self.metrics, **kwargs)
                    self.sessions[user_id].requests_made += 1

            except Exception as e:
                self.sessions[user_id].errors.append(
                    {"endpoint": endpoint, "error": str(e), "time": time.time()}
                )

            await self.think_time()


@pytest.mark.performance
@pytest.mark.load
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("RUN_LOAD_TESTS"),
    reason="Load tests are resource-intensive. Set RUN_LOAD_TESTS=1 to enable.",
)
class TestLoadScenarios:
    """Load test scenarios."""

    async def test_health_check_load(
        self,
        perf_client: AsyncClient,
    ):
        """Health endpoint should handle sustained load."""
        config = LoadTestConfig(
            concurrent_users=50,  # Reduced for CI
            duration_seconds=30,  # 30 seconds for CI
            ramp_up_seconds=5,
        )

        scenario = HealthCheckScenario(perf_client, config)
        metrics = await scenario.run()

        # Assertions
        assert metrics.success_rate >= 99.0, (
            f"Health check success rate ({metrics.success_rate:.2f}%) below 99%"
        )
        assert metrics.p95 < 0.5, f"Health check p95 ({metrics.p95:.3f}s) exceeds 500ms under load"

    async def test_mixed_endpoint_load(
        self,
        authed_perf_client: AsyncClient,
    ):
        """System should handle mixed endpoint load."""
        config = LoadTestConfig(
            concurrent_users=25,  # Reduced for CI
            duration_seconds=30,
            ramp_up_seconds=5,
        )

        scenario = MixedEndpointScenario(authed_perf_client, config)
        metrics = await scenario.run()

        # Calculate total requests
        total_requests = sum(s.requests_made for s in scenario.sessions)
        requests_per_second = total_requests / config.duration_seconds

        # Assertions
        assert metrics.success_rate >= 95.0, (
            f"Mixed endpoint success rate ({metrics.success_rate:.2f}%) below 95%"
        )
        assert requests_per_second > 5, (
            f"Throughput ({requests_per_second:.1f} req/s) below 5 req/s"
        )

    async def test_ramp_up_behavior(
        self,
        perf_client: AsyncClient,
    ):
        """System should handle gradual user ramp-up."""
        config = LoadTestConfig(
            concurrent_users=20,
            duration_seconds=20,
            ramp_up_seconds=10,  # Gradual ramp-up
        )

        scenario = HealthCheckScenario(perf_client, config)
        _metrics = await scenario.run()

        # All users should have made requests
        active_users = sum(1 for s in scenario.sessions if s.requests_made > 0)
        assert active_users >= config.concurrent_users * 0.9, (
            f"Only {active_users}/{config.concurrent_users} users were active"
        )


@pytest.mark.performance
@pytest.mark.load
@pytest.mark.asyncio
class TestConcurrentConnections:
    """Tests for concurrent connection handling."""

    async def test_burst_requests(
        self,
        perf_client: AsyncClient,
        metrics: PerformanceMetrics,
    ):
        """System should handle burst of simultaneous requests."""
        burst_size = 50

        tasks = [measure_request(perf_client, "GET", "/health", metrics) for _ in range(burst_size)]

        await asyncio.gather(*tasks, return_exceptions=True)

        assert metrics.success_rate >= 95.0, (
            f"Burst request success rate ({metrics.success_rate:.2f}%) below 95%"
        )

    async def test_sustained_concurrent_requests(
        self,
        perf_client: AsyncClient,
    ):
        """System should maintain performance under sustained concurrency."""
        concurrent_users = 20
        requests_per_user = 5
        all_metrics = PerformanceMetrics()

        async def user_requests(user_id: int):
            for _ in range(requests_per_user):
                try:
                    await measure_request(perf_client, "GET", "/health", all_metrics)
                except Exception:
                    pass
                await asyncio.sleep(0.1)

        tasks = [user_requests(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks)

        assert all_metrics.total_requests == concurrent_users * requests_per_user
        assert all_metrics.success_rate >= 99.0


@pytest.mark.performance
@pytest.mark.load
@pytest.mark.asyncio
class TestLoadTestMetrics:
    """Tests for load test metrics collection."""

    async def test_session_tracking(
        self,
        perf_client: AsyncClient,
    ):
        """Should track individual user sessions."""
        config = LoadTestConfig(
            concurrent_users=5,
            duration_seconds=5,
            ramp_up_seconds=1,
        )

        scenario = HealthCheckScenario(perf_client, config)
        await scenario.run()

        # Verify session tracking
        assert len(scenario.sessions) == config.concurrent_users
        for session in scenario.sessions:
            assert isinstance(session, UserSession)
            assert session.requests_made >= 0

    async def test_error_tracking(
        self,
        perf_client: AsyncClient,
    ):
        """Should track errors per session."""
        config = LoadTestConfig(
            concurrent_users=3,
            duration_seconds=5,
            ramp_up_seconds=1,
        )

        scenario = HealthCheckScenario(perf_client, config)
        metrics = await scenario.run()

        # Metrics should have captured all requests
        assert metrics.total_requests > 0
        # Errors list in metrics should exist
        assert isinstance(metrics.errors, list)
