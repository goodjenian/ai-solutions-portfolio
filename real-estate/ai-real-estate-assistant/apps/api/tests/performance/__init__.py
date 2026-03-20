"""Performance tests for AI Real Estate Assistant.

This module contains:
- API response time benchmarks
- Load testing scenarios
- Database performance tests
- Lighthouse configuration

Usage:
    # Run all performance tests
    pytest tests/performance -v -m performance

    # Run specific test categories
    pytest tests/performance -v -m "performance and not load"
    pytest tests/performance -v -m load
    pytest tests/performance -v -m database

    # Run with integration tests (requires running server)
    RUN_INTEGRATION_TESTS=1 pytest tests/performance -v -m performance

    # Run load tests (resource intensive)
    RUN_LOAD_TESTS=1 pytest tests/performance -v -m load

    # Run full benchmark suite
    python scripts/run_performance_tests.py --all
"""

__all__ = [
    "PerformanceMetrics",
    "measure_request",
    "concurrent_requests",
    "LoadTestConfig",
    "LoadTestScenario",
    "UserSession",
]
