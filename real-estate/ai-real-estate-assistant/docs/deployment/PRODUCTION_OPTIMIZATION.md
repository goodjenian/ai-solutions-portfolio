# Production Deployment Optimization

## Overview

This document describes the production optimization features implemented for Task #62, including caching, monitoring, connection pooling, and deployment strategies.

---

## 1. Caching Strategy

### Response Caching (`utils/response_cache.py`)

The application includes a comprehensive response caching layer with:

| Feature | Description |
|---------|-------------|
| Redis Backend | Distributed cache for multi-instance deployments |
| In-Memory Fallback | Automatic fallback when Redis unavailable |
| TTL Support | Configurable time-to-live per endpoint |
| Cache Warming | Pre-populate frequently accessed data |
| Key Generation | SHA256 hash of method + path + query + body |

**Configuration:**

```bash
# Enable caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
CACHE_REDIS_URL=redis://redis:6379
CACHE_PREFIX=api_cache
CACHE_MAX_MEMORY_MB=100
```

**Usage:**

```python
from utils.response_cache import cached_response

@router.get("/properties")
@cached_response(ttl_seconds=60)
async def get_properties(request: Request):
    # Response will be cached for 60 seconds
    ...
```

### Cache Invalidation

| Trigger | Action |
|---------|--------|
| Property Update | Invalidate `/api/v1/properties/*` |
| Lead Status Change | Invalidate `/api/v1/leads/*` |
| Document Upload | Invalidate `/api/v1/documents/*` |
| Manual | `DELETE /api/v1/admin/cache` |

---

## 2. Performance Monitoring

### Prometheus Metrics (`/metrics` endpoint)

**Application Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `app_info` | Gauge | Application version info |
| `app_health_status` | Gauge | Health status (0=unhealthy, 1=degraded, 2=healthy) |
| `app_uptime_seconds` | Gauge | Application uptime |
| `http_requests_total` | Counter | Total HTTP requests by method/path |
| `dependency_health_status` | Gauge | Dependency health by name |
| `dependency_latency_ms` | Gauge | Dependency check latency |

**Cache Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `cache_enabled` | Gauge | Cache enabled flag |
| `cache_size` | Gauge | Number of cached items |
| `cache_ttl_seconds` | Gauge | Configured TTL |
| `cache_hits_total` | Counter | Cache hit count |
| `cache_misses_total` | Counter | Cache miss count |

**Process Metrics (via psutil):**

| Metric | Type | Description |
|--------|------|-------------|
| `process_cpu_percent` | Gauge | CPU usage percentage |
| `process_memory_mb` | Gauge | Memory usage in MB |
| `process_threads` | Gauge | Number of threads |

### Grafana Dashboard

Import the dashboard from `deploy/monitoring/grafana-dashboard.json` to visualize:

- Application health status
- Request rates by endpoint
- Cache hit rates
- Dependency latencies
- Memory and CPU usage

### Health Check Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check (load balancer) |
| `/health?full=true` | Full dependency check |
| `/ready` | Readiness probe (Kubernetes) |

---

## 3. Connection Pooling

### Thread Pool (`utils/connection_pool.py`)

```bash
POOL_MAX_WORKERS=10
POOL_THREAD_NAME_PREFIX=pool-worker
```

### Redis Connection Pool

```bash
REDIS_POOL_SIZE=10
REDIS_MAX_OVERFLOW=20
REDIS_SOCKET_TIMEOUT=2.0
REDIS_SOCKET_CONNECT_TIMEOUT=2.0
```

### Database Connection Pool

```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=3600
```

---

## 4. Rate Limiting

### Configuration

```bash
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_RPM=600
```

### Redis-Backed Rate Limiting

When Redis is available, rate limiting is distributed across all instances:

```python
# In observability.py
RedisRateLimiter(
    redis_url=redis_url,
    max_requests=600,
    window_seconds=60,
)
```

### Response Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Remaining requests in window |
| `X-RateLimit-Reset` | Seconds until window resets |
| `Retry-After` | Seconds to wait after limit hit |

---

## 5. Auto-Scaling Configuration

### Kubernetes Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-real-estate-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-real-estate-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
```

### Docker Compose Scaling

```bash
# Scale backend to 3 instances
docker compose up --scale backend=3

# With load balancer
docker compose -f docker-compose.yml -f docker-compose.scale.yml up
```

---

## 6. Blue-Green Deployment

### Strategy

1. **Blue (Current)**: Running production traffic
2. **Green (New)**: New version being deployed

### Workflow

```bash
# 1. Deploy green environment
docker compose -f docker-compose.green.yml up -d

# 2. Run health checks
curl http://green:8000/health

# 3. Run smoke tests
pytest tests/integration/ --target=green

# 4. Switch traffic (update load balancer)
# 5. Monitor for issues
# 6. Rollback if needed or keep green as new blue
```

### Nginx Configuration

```nginx
upstream backend {
    least_conn;
    server blue:8000 weight 100;
    server green:8000 weight 0;
}

# To switch: update weights
# blue:8000 weight 0;
# green:8000 weight 100;
```

---

## 7. Monitoring Stack

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-real-estate-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected

      - alert: CacheHitRateLow
        expr: |
          rate(cache_hits_total[5m]) /
          (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: Cache hit rate below 50%

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: p95 latency above 2 seconds
```

---

## 8. Performance Targets

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| p95 Search Latency | < 2s | > 5s |
| p95 Chat Latency | < 8s | > 15s |
| Cache Hit Rate | > 80% | < 50% |
| Error Rate | < 1% | > 5% |
| CPU Usage | < 70% | > 90% |
| Memory Usage | < 80% | > 95% |

---

## 9. Deployment Checklist

### Pre-Deployment

- [ ] Run full CI: `make ci`
- [ ] Run security scan: `python scripts/security/local_scan.py`
- [ ] Run performance benchmarks: `python scripts/run_performance_tests.py --all`
- [ ] Review Grafana dashboards for anomalies
- [ ] Verify backup completed

### Deployment

- [ ] Tag release: `git tag -a v{version} -m "Release {version}"`
- [ ] Build images: `docker compose build`
- [ ] Push to registry
- [ ] Deploy green environment
- [ ] Run smoke tests
- [ ] Switch traffic

### Post-Deployment

- [ ] Monitor health endpoints
- [ ] Check error rates in Grafana
- [ ] Verify cache warming
- [ ] Monitor auto-scaling behavior

---

## 10. Troubleshooting

### High Latency

1. Check cache hit rate
2. Review slow query logs
3. Check LLM provider latency
4. Verify connection pool exhaustion

### Memory Issues

1. Check for memory leaks
2. Review cache size limits
3. Verify vector store memory usage
4. Check thread pool size

### Cache Misses

1. Verify Redis connectivity
2. Check TTL configuration
3. Review cache key generation
4. Monitor invalidation frequency
