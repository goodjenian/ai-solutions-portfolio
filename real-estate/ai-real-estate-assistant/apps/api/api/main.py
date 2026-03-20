import asyncio
import logging
import os
import signal
import warnings
from typing import Any

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module=r"langchain_google_genai\.chat_models",
)

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import get_api_key
from api.dependencies import get_vector_store
from api.health import get_git_info, get_health_status
from api.middleware.csrf import add_csrf_middleware
from api.middleware.error_handler import add_error_handlers
from api.middleware.request_size import add_request_size_limits
from api.middleware.security import add_security_headers
from api.observability import REQUEST_ID_HEADER, add_observability
from api.routers import (
    admin,
    agent_analytics,  # Task #56: Agent Performance Analytics
    agents,  # Task #45: Agent/Broker Integration
    anomalies,  # Task #53: Market Anomaly Detection
    auth,
    auth_jwt,  # JWT authentication endpoints
    chat,
    collections,  # Task #37: Property collections
    documents,  # Task #43: Document Management
    esignatures,  # Task #57: E-Signature Integration
    exports,
    favorites,  # Task #37: Property favorites
    leads,  # Task #55: Lead Scoring System
    market,  # Task #38: Price History & Trends
    metrics,  # Task #62: Production Monitoring
    prompt_templates,
    push,  # Task #63: Push Notifications
    saved_searches,
    search,
    tools,
    webhooks,  # Task #57: E-Signature Webhooks
)
from api.routers import (
    rag as rag_router,
)
from api.routers import (
    settings as settings_router,
)
from config.settings import get_settings
from notifications.email_service import (
    EmailConfig,
    EmailProvider,
    EmailService,
    EmailServiceFactory,
)
from notifications.scheduler import NotificationScheduler
from notifications.uptime_monitor import (
    UptimeMonitor,
    UptimeMonitorConfig,
    make_http_checker,
)
from utils.connection_pool import get_connection_pool_manager
from utils.json_logging import configure_json_logging
from utils.response_cache import CacheConfig, ResponseCache

configure_json_logging(logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.version,
    description="AI Real Estate Assistant API V4",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


add_observability(app, logger)
add_security_headers(app)
add_request_size_limits(app)
add_csrf_middleware(app)
add_error_handlers(app)

# Global scheduler instance
scheduler = None

# Graceful shutdown configuration
SHUTDOWN_DRAIN_SECONDS = int(os.getenv("SHUTDOWN_DRAIN_SECONDS", "30"))
SHUTDOWN_MAX_WAIT_SECONDS = int(os.getenv("SHUTDOWN_MAX_WAIT_SECONDS", "60"))


@app.on_event("startup")
async def startup_event():
    """Initialize application services on startup and setup signal handlers."""
    global scheduler
    from time import time

    # Set application start time for uptime metrics
    app.state.start_time = time()

    # Setup signal handlers for graceful shutdown (only in main thread)
    import threading

    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            if hasattr(signal, sig.name):
                signal.signal(sig, lambda s, f: None)  # Let FastAPI handle

    # 1. Initialize Vector Store
    logger.info("Initializing Vector Store...")
    vector_store = get_vector_store()
    if not vector_store:
        logger.warning(
            "Vector Store could not be initialized. "
            "Notifications relying on vector search will be disabled."
        )
    app.state.vector_store = vector_store

    # 1.5 Initialize Auth Database (if JWT auth enabled)
    if settings.auth_jwt_enabled:
        logger.info("Initializing Auth Database...")
        try:
            from db.database import init_db

            await init_db()
            logger.info("Auth Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Auth Database: {e}")

    # 2. Initialize Email Service
    logger.info("Initializing Email Service...")
    email_service = EmailServiceFactory.create_from_env()

    if not email_service:
        logger.warning(
            "No email configuration found in environment. "
            "Using dummy service (emails will not be sent)."
        )
        # Create dummy service for scheduler to function without crashing
        dummy_config = EmailConfig(
            provider=EmailProvider.CUSTOM,
            smtp_server="localhost",
            smtp_port=1025,
            username="dummy",
            password="dummy",
            from_email="noreply@example.com",
        )
        email_service = EmailService(dummy_config)

    # 3. Initialize and Start Scheduler
    logger.info("Starting Notification Scheduler...")
    try:
        scheduler = NotificationScheduler(
            email_service=email_service,
            vector_store=vector_store,
            poll_interval_seconds=60,
        )
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("Notification Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Notification Scheduler: {e}")

    # 4. Initialize Uptime Monitor (optional via env)
    try:
        enabled_raw = os.getenv("UPTIME_MONITOR_ENABLED", "false").strip().lower()
        enabled = enabled_raw in {"1", "true", "yes", "y", "on"}
        if enabled and email_service:
            health_url = os.getenv(
                "UPTIME_MONITOR_HEALTH_URL", "http://localhost:8000/health"
            ).strip()
            to_email = (
                os.getenv("UPTIME_MONITOR_EMAIL_TO", "ops@example.com").strip() or "ops@example.com"
            )
            interval = float(os.getenv("UPTIME_MONITOR_INTERVAL", "60").strip() or "60")
            threshold = int(os.getenv("UPTIME_MONITOR_FAIL_THRESHOLD", "3").strip() or "3")
            cooldown = float(os.getenv("UPTIME_MONITOR_COOLDOWN_SECONDS", "1800").strip() or "1800")
            checker = make_http_checker(health_url, timeout=3.0)
            mon_cfg = UptimeMonitorConfig(
                interval_seconds=interval,
                fail_threshold=threshold,
                alert_cooldown_seconds=cooldown,
                to_email=to_email,
            )
            uptime_monitor = UptimeMonitor(
                checker=checker, email_service=email_service, config=mon_cfg, logger=logger
            )
            uptime_monitor.start()
            app.state.uptime_monitor = uptime_monitor
            logger.info(
                "Uptime Monitor started url=%s to=%s interval=%s", health_url, to_email, interval
            )
    except Exception as e:
        logger.error(f"Failed to start Uptime Monitor: {e}")

    # 5. Initialize Response Cache (TASK-017: Production Deployment Optimization)
    logger.info("Initializing Response Cache...")
    try:
        cache_settings = CacheConfig(
            enabled=getattr(settings, "cache_enabled", True),
            ttl_seconds=getattr(settings, "cache_ttl_seconds", 300),
            prefix=getattr(settings, "cache_prefix", "api_cache"),
            max_memory_mb=getattr(settings, "cache_max_memory_mb", 100),
            stale_while_revalidate=getattr(settings, "cache_stale_while_revalidate", False),
        )
        redis_url = getattr(settings, "cache_redis_url", None)
        response_cache = ResponseCache(config=cache_settings, redis_url=redis_url)
        app.state.response_cache = response_cache
        logger.info("Response Cache initialized: %s", response_cache.get_stats())
    except Exception as e:
        logger.warning(f"Failed to initialize Response Cache: {e}")

    # 6. Initialize Connection Pool Manager (TASK-017)
    logger.info("Initializing Connection Pool Manager...")
    try:
        pool_manager = get_connection_pool_manager()
        app.state.pool_manager = pool_manager
        logger.info("Connection Pool Manager initialized: %s", pool_manager.get_stats())
    except Exception as e:
        logger.warning(f"Failed to initialize Connection Pool Manager: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on shutdown with graceful drain period.

    This handler:
    1. Logs the shutdown initiation
    2. Waits for a drain period to allow in-flight requests to complete
    3. Stops background services (scheduler, monitors)
    4. Closes database/vector store connections
    5. Logs completion of shutdown
    """
    logger.info("Graceful shutdown initiated...")
    shutdown_start_time = asyncio.get_event_loop().time()

    # Step 1: Stop accepting new requests (handled by uvicorn)
    # We just need to drain in-flight requests during this period

    # Step 2: Stop Uptime Monitor first (doesn't depend on other services)
    mon = getattr(app.state, "uptime_monitor", None)
    if mon:
        logger.info("Stopping Uptime Monitor...")
        try:
            mon.stop()
            logger.info("Uptime Monitor stopped.")
        except Exception as e:
            logger.error(f"Error stopping Uptime Monitor: {e}")

    # Step 3: Stop Notification Scheduler
    if scheduler:
        logger.info("Stopping Notification Scheduler...")
        try:
            scheduler.stop()
            logger.info("Notification Scheduler stopped.")
        except Exception as e:
            logger.error(f"Error stopping Notification Scheduler: {e}")

    # Step 4: Wait for drain period to allow in-flight requests to complete
    if SHUTDOWN_DRAIN_SECONDS > 0:
        logger.info(f"Waiting {SHUTDOWN_DRAIN_SECONDS}s drain period for in-flight requests...")
        try:
            await asyncio.sleep(SHUTDOWN_DRAIN_SECONDS)
        except Exception as e:
            logger.warning(f"Drain period interrupted: {e}")

    # Step 5: Close vector store connection
    vector_store = getattr(app.state, "vector_store", None)
    if vector_store:
        logger.info("Closing Vector Store connection...")
        try:
            # ChromaDB doesn't need explicit closing, but if we had
            # a database connection we would close it here
            if hasattr(vector_store, "close"):
                await vector_store.close()
            logger.info("Vector Store connection closed.")
        except Exception as e:
            logger.error(f"Error closing Vector Store: {e}")

    # Step 6: Close rate limiter connections if using Redis
    rate_limiter = getattr(app.state, "rate_limiter", None)
    if rate_limiter and hasattr(rate_limiter, "_redis_client"):
        redis_client = rate_limiter._redis_client
        if redis_client:
            logger.info("Closing Redis connection...")
            try:
                await redis_client.aclose() if hasattr(
                    redis_client, "aclose"
                ) else redis_client.close()
                logger.info("Redis connection closed.")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    # Step 7: Clear response cache (TASK-017)
    response_cache = getattr(app.state, "response_cache", None)
    if response_cache:
        logger.info("Clearing Response Cache...")
        try:
            await response_cache.clear_all()
            logger.info("Response Cache cleared.")
        except Exception as e:
            logger.error(f"Error clearing Response Cache: {e}")

    # Step 8: Close connection pools (TASK-017)
    pool_manager = getattr(app.state, "pool_manager", None)
    if pool_manager:
        logger.info("Closing connection pools...")
        try:
            pool_manager.close_all()
            logger.info("Connection pools closed.")
        except Exception as e:
            logger.error(f"Error closing connection pools: {e}")

    shutdown_elapsed = asyncio.get_event_loop().time() - shutdown_start_time
    logger.info(f"Graceful shutdown completed in {shutdown_elapsed:.2f}s")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER],
)

# Include Routers
app.include_router(search.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(chat.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(rag_router.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(settings_router.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(tools.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(prompt_templates.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(admin.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(exports.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(auth.router, prefix="/api/v1")
# Task #62: Prometheus metrics endpoint (no auth required for monitoring)
app.include_router(metrics.router)

# JWT Auth Router (conditionally enabled)
if settings.auth_jwt_enabled:
    app.include_router(auth_jwt.router, prefix="/api/v1")
    # Saved searches requires JWT auth
    app.include_router(saved_searches.router, prefix="/api/v1")
    # Task #37: Favorites and Collections require JWT auth
    app.include_router(collections.router, prefix="/api/v1")
    app.include_router(favorites.router, prefix="/api/v1")
    # Task #38: Market analytics (price history, trends, indicators)
    app.include_router(market.router, prefix="/api/v1")
    app.include_router(anomalies.router, prefix="/api/v1")
    # Task #55: Lead Scoring System
    app.include_router(leads.router, prefix="/api/v1")
    # Task #56: Agent Performance Analytics
    app.include_router(agent_analytics.router, prefix="/api/v1")
    # Task #63: Push Notifications
    app.include_router(push.router, prefix="/api/v1")
    # Task #45: Agent/Broker Integration
    app.include_router(agents.router, prefix="/api/v1")
    # Task #43: Document Management System
    app.include_router(documents.router, prefix="/api/v1")
    # Task #57: E-Signature Integration
    if settings.auth_jwt_enabled:
        app.include_router(esignatures.router, prefix="/api/v1")
        app.include_router(webhooks.esignatures.router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check(include_dependencies: bool = True):
    """
    Health check endpoint to verify API status.

    Args:
        include_dependencies: Whether to check dependency health (vector store, Redis, LLM providers)

    Returns:
        Comprehensive health status including dependencies
    """
    health = await get_health_status(include_dependencies=include_dependencies)

    # Convert to dict for JSON response
    response: dict[str, str | float | dict[str, Any]] = {
        "status": health.status.value,
        "version": health.version,
        "timestamp": health.timestamp,
        "uptime_seconds": health.uptime_seconds,
    }

    if health.dependencies:
        response["dependencies"] = {
            name: {
                "status": dep.status.value,
                "message": dep.message,
                "latency_ms": dep.latency_ms,
            }
            for name, dep in health.dependencies.items()
        }

    # Add git info for production deployments
    git_info = get_git_info()
    if git_info.get("commit") != "unknown":
        response["git"] = git_info

    # Return appropriate HTTP status based on health
    from fastapi import status as http_status

    status_code = http_status.HTTP_200_OK
    if health.status.value == "unhealthy":
        status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    elif health.status.value == "degraded":
        status_code = http_status.HTTP_200_OK  # Degraded is still 200, with info

    from fastapi.responses import JSONResponse

    return JSONResponse(content=response, status_code=status_code)


@app.get("/api/v1/verify-auth", dependencies=[Depends(get_api_key)], tags=["Auth"])
async def verify_auth():
    """
    Verify API key authentication.
    """
    return {"message": "Authenticated successfully", "valid": True}


@app.get("/metrics", tags=["System"])
async def metrics_endpoint():
    """
    Prometheus-compatible metrics endpoint (TASK-017).

    Returns application metrics in Prometheus text format.
    """
    from time import time

    metrics = []
    metrics.append("# HELP api_requests_total Total number of API requests")
    metrics.append("# TYPE api_requests_total counter")

    # Get request metrics from app state
    if hasattr(app.state, "metrics"):
        for key, count in app.state.metrics.items():
            method, path = key.split(" ", 1) if " " in key else ("UNKNOWN", key)
            # Sanitize path for Prometheus label
            safe_path = path.replace("/", "_").strip("_") or "root"
            metrics.append(f'api_requests_total{{method="{method}",path="{safe_path}"}} {count}')

    # Add cache metrics if available
    response_cache = getattr(app.state, "response_cache", None)
    if response_cache:
        cache_stats = response_cache.get_stats()
        metrics.append("\n# HELP api_cache_size Current number of cached entries")
        metrics.append("# TYPE api_cache_size gauge")
        metrics.append(f"api_cache_size {cache_stats.get('size', 0)}")
        metrics.append("\n# HELP api_cache_enabled Whether caching is enabled")
        metrics.append("# TYPE api_cache_enabled gauge")
        metrics.append(f"api_cache_enabled {1 if cache_stats.get('enabled') else 0}")

    # Add uptime metric
    if hasattr(app.state, "start_time"):
        uptime = time() - app.state.start_time
        metrics.append("\n# HELP api_uptime_seconds Application uptime in seconds")
        metrics.append("# TYPE api_uptime_seconds gauge")
        metrics.append(f"api_uptime_seconds {uptime:.2f}")

    return "\n".join(metrics), 200, {"Content-Type": "text/plain; version=0.0.4"}
