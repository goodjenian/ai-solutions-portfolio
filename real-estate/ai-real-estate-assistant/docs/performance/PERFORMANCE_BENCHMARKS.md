# Performance Benchmark Results

## Overview

This document summarizes the performance benchmark suite created for Task #60.

## Test Files Created

| File | Description | Tests |
|------|-------------|-------|
| `tests/performance/conftest.py` | Performance test fixtures and metrics utilities | N/A |
| `tests/performance/test_api_response_times.py` | API endpoint response time benchmarks | 13 |
| `tests/performance/test_load.py` | Load testing scenarios | 7 |
| `tests/performance/test_database.py` | Database performance tests | 18 |
| `lighthouse.config.js` | Desktop Lighthouse configuration | N/A |
| `lighthouse.mobile.config.js` | Mobile Lighthouse configuration | N/A |
| `scripts/run_performance_tests.py` | Benchmark runner script | N/A |

## Performance Thresholds

### API Response Times

| Endpoint | p95 Threshold | Avg Threshold | Success Rate |
|----------|---------------|---------------|--------------|
| Health | < 100ms | < 50ms | 100% |
| Search | < 2s | < 1s | 99% |
| Chat | < 8s | < 5s | 95% |
| Documents | < 5s (10MB) | < 2s | 99% |
| Leads | < 1s | < 500ms | 99% |

### Lighthouse Scores

| Category | Desktop | Mobile |
|----------|---------|--------|
| Performance | ≥ 90 | ≥ 85 |
| Accessibility | ≥ 90 | ≥ 90 |
| Best Practices | ≥ 90 | ≥ 90 |
| SEO | ≥ 80 | ≥ 80 |

### Core Web Vitals

| Metric | Threshold |
|--------|-----------|
| First Contentful Paint | < 2s |
| Largest Contentful Paint | < 2.5s |
| Cumulative Layout Shift | < 0.1 |
| Total Blocking Time | < 300ms |
| Speed Index | < 3s |

## Test Results (Baseline)

```
Platform: win32
Python: 3.13.2
Date: 2026-03-19

Performance Tests Summary:
- Total: 23 passed, 15 skipped
- Duration: ~15 seconds

Skipped Tests:
- Integration tests (require RUN_INTEGRATION_TESTS=1)
- Load tests (require RUN_LOAD_TESTS=1)
- Database query tests (require database connection)
```

## Running Benchmarks

### Quick Test (Health Endpoints Only)

```bash
cd apps/api
pytest tests/performance -v -m performance
```

### With Integration Tests

```bash
# Requires running backend at localhost:8000
RUN_INTEGRATION_TESTS=1 pytest tests/performance -v -m performance
```

### Load Tests (Resource Intensive)

```bash
# Requires running backend
RUN_LOAD_TESTS=1 pytest tests/performance/test_load.py -v
```

### Full Benchmark Suite

```bash
# From project root
python scripts/run_performance_tests.py --all
```

### Lighthouse Audits

```bash
cd apps/web
npx lighthouse http://localhost:3000 --config-path=lighthouse.config.js
```

## Test Categories

### 1. API Response Time Tests (`test_api_response_times.py`)

- **Health Endpoints**: Response time < 100ms
- **Search API**: p95 < 2s for property searches
- **Chat API**: p95 < 8s (includes LLM processing)
- **Document API**: Upload < 5s for 10MB files
- **Leads API**: CRUD operations < 1s

### 2. Load Tests (`test_load.py`)

- **Concurrent Users**: Tests with 50-100 concurrent users
- **Sustained Load**: 30-60 second sustained load tests
- **Burst Requests**: Simultaneous request bursts
- **Mixed Endpoints**: Realistic traffic distribution

### 3. Database Tests (`test_database.py`)

- **Query Performance**: Verify indexes are effective
- **N+1 Detection**: Patterns for detecting N+1 queries
- **Connection Pool**: Verify pool behavior under load
- **Query Complexity**: Execution plan analysis

### 4. Lighthouse Audits

- **Desktop**: Full audit with desktop emulation
- **Mobile**: Audit with mobile throttling
- **Core Web Vitals**: LCP, FID, CLS thresholds

## Metrics Collection

The `PerformanceMetrics` class provides:

```python
metrics = PerformanceMetrics()
# ... make requests ...

print(f"Total: {metrics.total_requests}")
print(f"Success Rate: {metrics.success_rate:.2f}%")
print(f"p50: {metrics.p50:.3f}s")
print(f"p95: {metrics.p95:.3f}s")
print(f"p99: {metrics.p99:.3f}s")
print(f"Avg: {metrics.avg:.3f}s")
```

## CI Integration

Performance tests can be integrated into CI:

```yaml
# .github/workflows/performance.yml
- name: Run Performance Tests
  run: |
    cd apps/api
    pytest tests/performance -v -m "performance and not load"
```

For full benchmarks with load testing, use scheduled runs.

## Notes

1. **Baseline Performance**: Tests verify system meets baseline thresholds
2. **Regression Detection**: Failures indicate performance regressions
3. **Resource Usage**: Load tests are skipped by default to save resources
4. **Real Database**: Query performance tests require actual database connection
