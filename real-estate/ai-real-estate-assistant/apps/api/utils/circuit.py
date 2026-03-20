"""
Circuit breaker pattern implementation for LLM provider calls.

Prevents cascading failures by:
1. Tracking failure rates per provider
2. Opening circuit after threshold exceeded
3. Allowing recovery after cooldown period
4. Providing fallback to alternative providers

State transitions:
CLOSED -> OPEN (failure threshold exceeded)
OPEN -> HALF_OPEN (cooldown period elapsed)
HALF_OPEN -> CLOSED (successful probe)
HALF_OPEN -> OPEN (failed probe)
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if provider has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes to close circuit from half-open
    timeout_seconds: float = 60.0  # Cooldown before half-open
    half_open_max_calls: int = 1  # Max calls in half-open state
    rolling_window_size: int = 100  # Size of rolling result window


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0  # Calls rejected due to open circuit
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_state: CircuitState = CircuitState.CLOSED
    state_changed_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        total = self.successful_calls + self.failed_calls
        if total == 0:
            return 0.0
        return self.failed_calls / total


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, provider: str, cooldown_remaining: float):
        self.provider = provider
        self.cooldown_remaining = cooldown_remaining
        super().__init__(
            f"Circuit breaker open for provider '{provider}'. "
            f"Retry after {cooldown_remaining:.1f} seconds."
        )


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.

    Usage:
        breaker = CircuitBreaker("openai", config)

        try:
            result = await breaker.call(lambda: make_api_call())
        except CircuitBreakerOpenError:
            # Handle open circuit - use fallback
            result = await fallback_call()
    """

    def __init__(
        self,
        provider: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            provider: Provider name for logging/tracking
            config: Circuit breaker configuration
        """
        self.provider = provider
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._rolling_results: deque[bool] = deque(maxlen=self.config.rolling_window_size)
        self._half_open_calls = 0

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.stats.last_failure_time is None:
            return True

        elapsed = (datetime.now(tz=UTC) - self.stats.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional args for function
            **kwargs: Keyword args for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function call raises an exception
        """
        async with self._lock:
            self.stats.total_calls += 1

            # Check circuit state
            if self.stats.current_state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    # Transition to half-open
                    logger.info(
                        "Circuit breaker for '%s': OPEN -> HALF_OPEN (after cooldown)",
                        self.provider,
                    )
                    self.stats.current_state = CircuitState.HALF_OPEN
                    self.stats.state_changed_at = datetime.now(tz=UTC)
                    self._half_open_calls = 0
                else:
                    # Circuit still open
                    # last_failure_time is guaranteed to be set here since _should_attempt_reset() returned False
                    last_failure = cast(datetime, self.stats.last_failure_time)
                    cooldown_remaining = (
                        self.config.timeout_seconds
                        - (datetime.now(tz=UTC) - last_failure).total_seconds()
                    )
                    self.stats.rejected_calls += 1
                    raise CircuitBreakerOpenError(self.provider, cooldown_remaining)

            if self.stats.current_state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls > self.config.half_open_max_calls:
                    # Too many calls in half-open, open again
                    logger.warning(
                        "Circuit breaker for '%s': HALF_OPEN -> OPEN (too many probes)",
                        self.provider,
                    )
                    self.stats.current_state = CircuitState.OPEN
                    self.stats.state_changed_at = datetime.now(tz=UTC)
                    self.stats.rejected_calls += 1
                    raise CircuitBreakerOpenError(self.provider, self.config.timeout_seconds)

        # Execute the function call
        start = time.perf_counter()
        try:
            result: T = await func(*args, **kwargs)  # type: ignore[misc]
            elapsed = (time.perf_counter() - start) * 1000

            async with self._lock:
                self._on_success(elapsed)

            return result

        except Exception:
            elapsed = (time.perf_counter() - start) * 1000

            async with self._lock:
                self._on_failure(elapsed)

            raise

    def _on_success(self, elapsed_ms: float) -> None:
        """Handle successful call."""
        self.stats.successful_calls += 1
        self.stats.last_success_time = datetime.now(tz=UTC)
        self._rolling_results.append(True)

        # Check if we should close circuit from half-open
        if self.stats.current_state == CircuitState.HALF_OPEN:
            recent_successes = sum(1 for r in self._rolling_results if r)
            if recent_successes >= self.config.success_threshold:
                logger.info(
                    "Circuit breaker for '%s': HALF_OPEN -> CLOSED (recovered)",
                    self.provider,
                )
                self.stats.current_state = CircuitState.CLOSED
                self.stats.state_changed_at = datetime.now(tz=UTC)
                self._half_open_calls = 0

    def _on_failure(self, elapsed_ms: float) -> None:
        """Handle failed call."""
        self.stats.failed_calls += 1
        self.stats.last_failure_time = datetime.now(tz=UTC)
        self._rolling_results.append(False)

        # Check if we should open circuit
        recent_failures = sum(1 for r in self._rolling_results if not r)
        if (
            recent_failures >= self.config.failure_threshold
            and self.stats.current_state != CircuitState.OPEN
        ):
            logger.warning(
                "Circuit breaker for '%s': %s -> OPEN (threshold exceeded)",
                self.provider,
                self.stats.current_state.value.upper(),
            )
            self.stats.current_state = CircuitState.OPEN
            self.stats.state_changed_at = datetime.now(tz=UTC)

    def get_stats(self) -> dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dict with current stats
        """
        return {
            "provider": self.provider,
            "state": self.stats.current_state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "rejected_calls": self.stats.rejected_calls,
            "failure_rate": self.stats.failure_rate(),
            "last_failure_time": self.stats.last_failure_time.isoformat()
            if self.stats.last_failure_time
            else None,
            "last_success_time": self.stats.last_success_time.isoformat()
            if self.stats.last_success_time
            else None,
            "state_changed_at": self.stats.state_changed_at.isoformat(),
        }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        logger.info("Circuit breaker for '%s': reset to CLOSED", self.provider)
        self.stats = CircuitBreakerStats()
        self._rolling_results.clear()
        self._half_open_calls = 0


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Provides a centralized way to get/create circuit breakers for different providers.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
        self._config: Optional[CircuitBreakerConfig] = None

    def set_config(self, config: CircuitBreakerConfig) -> None:
        """
        Set default configuration for new circuit breakers.

        Args:
            config: Default circuit breaker configuration
        """
        self._config = config

    async def get_breaker(self, provider: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for provider.

        Args:
            provider: Provider name

        Returns:
            CircuitBreaker instance
        """
        async with self._lock:
            if provider not in self._breakers:
                self._breakers[provider] = CircuitBreaker(provider, self._config)
            return self._breakers[provider]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get stats for all circuit breakers.

        Returns:
            Dict mapping provider name to stats
        """
        return {provider: breaker.get_stats() for provider, breaker in self._breakers.items()}

    async def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        async with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global circuit breaker registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """
    Get the global circuit breaker registry.

    Returns:
        CircuitBreakerRegistry instance
    """
    return _registry


async def execute_with_circuit_breaker(
    provider: str,
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Execute function with circuit breaker protection.

    Convenience function that gets/creates breaker and executes call.

    Args:
        provider: Provider name
        func: Function to call
        *args: Positional args for function
        **kwargs: Keyword args for function

    Returns:
        Function result

    Raises:
        CircuitBreakerOpenError: If circuit is open
    """
    registry = get_circuit_breaker_registry()
    breaker = await registry.get_breaker(provider)
    return await breaker.call(func, *args, **kwargs)
