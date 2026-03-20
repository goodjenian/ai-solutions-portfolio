"""
Connection pool configuration for database and cache clients.

This module provides production-ready connection pooling for:
- ChromaDB client connections
- Redis connections (shared with observability module)
- Thread pool for concurrent operations

(TASK-017: Production Deployment Optimization)
"""

from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pools."""

    # Thread pool for concurrent operations
    max_workers: int = 10
    thread_name_prefix: str = "pool-worker"

    # ChromaDB client pool
    chroma_pool_size: int = 10
    chroma_max_overflow: int = 20
    chroma_pool_timeout: float = 30.0
    chroma_pool_recycle: float = 3600.0

    # Redis connection pool
    redis_pool_size: int = 10
    redis_max_overflow: int = 20
    redis_socket_timeout: float = 2.0
    redis_socket_connect_timeout: float = 2.0

    @classmethod
    def from_env(cls) -> "PoolConfig":
        """Create pool configuration from environment variables."""
        return cls(
            max_workers=int(os.getenv("POOL_MAX_WORKERS", "10")),
            thread_name_prefix=os.getenv("POOL_THREAD_NAME_PREFIX", "pool-worker"),
            chroma_pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            chroma_max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            chroma_pool_timeout=float(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30")),
            chroma_pool_recycle=float(os.getenv("DB_POOL_RECYCLE_SECONDS", "3600")),
            redis_pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
            redis_max_overflow=int(os.getenv("REDIS_MAX_OVERFLOW", "20")),
            redis_socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.0")),
            redis_socket_connect_timeout=float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0")),
        )


class ConnectionPoolManager:
    """
    Centralized connection pool manager.

    Manages thread pools and connection pools for database and cache clients.
    """

    _instance: Optional["ConnectionPoolManager"] = None
    _lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "ConnectionPoolManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._config = PoolConfig.from_env()
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._redis_pool: Optional[Any] = None
        self._redis_pool_initialized = False
        self._initialized = True

    def get_thread_pool(self) -> ThreadPoolExecutor:
        """Get or create the thread pool for concurrent operations."""
        if self._thread_pool is None:
            with threading.Lock():
                if self._thread_pool is None:
                    self._thread_pool = ThreadPoolExecutor(
                        max_workers=self._config.max_workers,
                        thread_name_prefix=self._config.thread_name_prefix,
                    )
                    logger.info(
                        "Created thread pool: max_workers=%d",
                        self._config.max_workers,
                    )
        return self._thread_pool

    def get_redis_connection_pool(self, redis_url: str) -> Optional[Any]:
        """
        Get or create a Redis connection pool.

        Args:
            redis_url: Redis connection URL

        Returns:
            Redis connection pool or None if redis package not available
        """
        if self._redis_pool is None:
            if self._redis_pool_initialized:
                return None
            with threading.Lock():
                if self._redis_pool is None:
                    self._redis_pool_initialized = True
                    try:
                        import redis

                        self._redis_pool = redis.ConnectionPool.from_url(
                            redis_url,
                            max_connections=self._config.redis_pool_size
                            + self._config.redis_max_overflow,
                            socket_timeout=self._config.redis_socket_timeout,
                            socket_connect_timeout=self._config.redis_socket_connect_timeout,
                        )
                        logger.info(
                            "Created Redis connection pool: max_connections=%d",
                            self._config.redis_pool_size + self._config.redis_max_overflow,
                        )
                    except ImportError:
                        logger.warning("Redis package not installed")
                        return None
                    except Exception as e:
                        logger.warning("Failed to create Redis pool: %s", e)
                        return None
        return self._redis_pool

    def get_redis_client(self, redis_url: str) -> Optional[Any]:
        """
        Get a Redis client with connection pooling.

        Args:
            redis_url: Redis connection URL

        Returns:
            Redis client or None if unavailable
        """
        pool = self._redis_pool
        if pool is None:
            return None

        try:
            import redis

            return redis.Redis(connection_pool=pool)
        except Exception as e:
            logger.warning("Failed to create Redis client: %s", e)
            return None

    def close_all(self) -> None:
        """Close all connection pools and thread pools."""
        if self._thread_pool is not None:
            logger.info("Shutting down thread pool...")
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None

        if self._redis_pool is not None:
            logger.info("Disconnecting Redis connection pool...")
            try:
                self._redis_pool.disconnect()
            except Exception as e:
                logger.warning("Error disconnecting Redis pool: %s", e)
            self._redis_pool = None
            self._redis_pool_initialized = False

    def get_stats(self) -> dict[str, Any]:
        """Get connection pool statistics."""
        stats = {
            "config": {
                "max_workers": self._config.max_workers,
                "chroma_pool_size": self._config.chroma_pool_size,
                "redis_pool_size": self._config.redis_pool_size,
            },
            "thread_pool_active": self._thread_pool is not None,
            "redis_pool_active": self._redis_pool is not None,
        }

        # Add Redis pool stats if available
        if self._redis_pool is not None:
            try:
                stats["redis_pool"] = {
                    "created_connections": getattr(self._redis_pool, "created_connections", "N/A"),
                    "available_connections": getattr(
                        self._redis_pool, "available_connections", "N/A"
                    ),
                }
            except Exception:
                pass

        return stats


# Global connection pool manager instance
_connection_pool_manager: Optional[ConnectionPoolManager] = None
_manager_lock = threading.Lock()


def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance."""
    global _connection_pool_manager
    if _connection_pool_manager is None:
        with _manager_lock:
            if _connection_pool_manager is None:
                _connection_pool_manager = ConnectionPoolManager()
    return _connection_pool_manager


def close_connection_pools() -> None:
    """Close all connection pools. Call this on application shutdown."""
    global _connection_pool_manager
    if _connection_pool_manager is not None:
        _connection_pool_manager.close_all()
        _connection_pool_manager = None
