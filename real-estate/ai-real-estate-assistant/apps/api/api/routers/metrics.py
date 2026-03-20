"""
Prometheus metrics endpoint for production monitoring.

This module provides metrics in Prometheus format for scraping by
monitoring systems like Grafana, Datadog, or Prometheus Server.

Metrics exposed:
- HTTP request latency (histogram)
- HTTP request count (counter)
- Active connections (gauge)
- Cache hit/miss ratio
- Rate limit events
- LLM API latency
- Vector store query latency
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


def format_prometheus_metric(
    name: str,
    value: float | int,
    metric_type: str = "gauge",
    labels: dict[str, str] | None = None,
    help_text: str = "",
) -> str:
    """Format a metric in Prometheus text format."""
    label_str = ""
    if labels:
        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        label_str = "{" + ",".join(label_pairs) + "}"

    lines = []
    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} {metric_type}")
    lines.append(f"{name}{label_str} {value}")

    return "\n".join(lines)


@router.get("/metrics")
async def get_metrics(request: Request) -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    """
    metrics_lines = []

    # Application info
    metrics_lines.append(
        format_prometheus_metric(
            "app_info",
            1,
            metric_type="gauge",
            labels={"version": "4.0.0", "app": "ai-real-estate-assistant"},
            help_text="Application information",
        )
    )

    # Get app state metrics
    app_metrics: dict[str, int] = getattr(request.app.state, "metrics", {})

    # HTTP request counts
    for key, count in app_metrics.items():
        parts = key.split(" ", 1)
        method = parts[0] if len(parts) > 0 else "unknown"
        path = parts[1] if len(parts) > 1 else "unknown"
        # Normalize path for metrics (replace IDs with placeholder)
        normalized_path = path
        for segment in path.split("/"):
            if segment.isdigit() or (len(segment) > 10 and "-" in segment):
                normalized_path = normalized_path.replace(segment, "{id}")

        metrics_lines.append(
            format_prometheus_metric(
                "http_requests_total",
                count,
                metric_type="counter",
                labels={"method": method, "path": normalized_path},
                help_text="Total HTTP requests",
            )
        )

    # Rate limiter stats
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if rate_limiter:
        metrics_lines.append(
            format_prometheus_metric(
                "rate_limiter_enabled",
                1,
                metric_type="gauge",
                help_text="Rate limiter is enabled",
            )
        )

    # Cache stats
    response_cache = getattr(request.app.state, "response_cache", None)
    if response_cache:
        cache_stats = response_cache.get_stats()
        metrics_lines.append(
            format_prometheus_metric(
                "cache_enabled",
                1 if cache_stats.get("enabled") else 0,
                metric_type="gauge",
                help_text="Response cache is enabled",
            )
        )
        metrics_lines.append(
            format_prometheus_metric(
                "cache_size",
                cache_stats.get("size", 0),
                metric_type="gauge",
                labels={"backend": cache_stats.get("backend", "unknown")},
                help_text="Number of cached responses",
            )
        )
        metrics_lines.append(
            format_prometheus_metric(
                "cache_ttl_seconds",
                cache_stats.get("ttl_seconds", 0),
                metric_type="gauge",
                help_text="Cache TTL in seconds",
            )
        )

    # Connection pool stats
    try:
        from utils.connection_pool import get_connection_pool_manager

        pool_manager = get_connection_pool_manager()
        pool_stats = pool_manager.get_stats()

        metrics_lines.append(
            format_prometheus_metric(
                "pool_thread_pool_active",
                1 if pool_stats.get("thread_pool_active") else 0,
                metric_type="gauge",
                help_text="Thread pool is active",
            )
        )
        metrics_lines.append(
            format_prometheus_metric(
                "pool_redis_pool_active",
                1 if pool_stats.get("redis_pool_active") else 0,
                metric_type="gauge",
                help_text="Redis connection pool is active",
            )
        )

        config = pool_stats.get("config", {})
        metrics_lines.append(
            format_prometheus_metric(
                "pool_max_workers",
                config.get("max_workers", 0),
                metric_type="gauge",
                help_text="Maximum worker threads",
            )
        )
    except Exception as e:
        logger.debug("Could not get pool stats: %s", e)

    # Health check metrics
    try:
        from api.health import get_health_status

        health = await get_health_status(include_dependencies=True)

        # Overall health status (0=unhealthy, 1=degraded, 2=healthy)
        status_value = {"healthy": 2, "degraded": 1, "unhealthy": 0}.get(health.status.value, 0)
        metrics_lines.append(
            format_prometheus_metric(
                "app_health_status",
                status_value,
                metric_type="gauge",
                help_text="Application health status (0=unhealthy, 1=degraded, 2=healthy)",
            )
        )

        # Uptime
        metrics_lines.append(
            format_prometheus_metric(
                "app_uptime_seconds",
                health.uptime_seconds,
                metric_type="gauge",
                help_text="Application uptime in seconds",
            )
        )

        # Dependency health
        for dep_name, dep_health in health.dependencies.items():
            dep_status = {"healthy": 2, "degraded": 1, "unhealthy": 0}.get(
                dep_health.status.value, 0
            )
            metrics_lines.append(
                format_prometheus_metric(
                    "dependency_health_status",
                    dep_status,
                    metric_type="gauge",
                    labels={"dependency": dep_name},
                    help_text="Dependency health status",
                )
            )
            if dep_health.latency_ms is not None:
                metrics_lines.append(
                    format_prometheus_metric(
                        "dependency_latency_ms",
                        dep_health.latency_ms,
                        metric_type="gauge",
                        labels={"dependency": dep_name},
                        help_text="Dependency check latency in milliseconds",
                    )
                )
    except Exception as e:
        logger.debug("Could not get health metrics: %s", e)

    # Process metrics (if psutil available)
    try:
        import psutil

        process = psutil.Process()
        metrics_lines.append(
            format_prometheus_metric(
                "process_cpu_percent",
                process.cpu_percent(),
                metric_type="gauge",
                help_text="Process CPU usage percentage",
            )
        )
        metrics_lines.append(
            format_prometheus_metric(
                "process_memory_mb",
                process.memory_info().rss / 1024 / 1024,
                metric_type="gauge",
                help_text="Process memory usage in MB",
            )
        )
        metrics_lines.append(
            format_prometheus_metric(
                "process_threads",
                process.num_threads(),
                metric_type="gauge",
                help_text="Number of process threads",
            )
        )
    except ImportError:
        pass

    # Combine all metrics
    metrics_text = "\n".join(metrics_lines) + "\n"

    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
