"""
Circuit breaker pattern implementation for Claude API resilience.

This module provides a production-grade CircuitBreaker implementation with
exponential backoff, Prometheus metrics, and comprehensive state tracking
for handling API failures gracefully.

The circuit breaker follows the classic pattern:
  CLOSED -> OPEN -> HALF_OPEN -> CLOSED (or back to OPEN)

- CLOSED: Normal operation, requests pass through.
- OPEN: Too many failures, requests fail fast without calling the function.
- HALF_OPEN: Allowing limited requests to test if service recovered.
"""
from __future__ import annotations

import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from app.core.exceptions import LLMError

logger = logging.getLogger("truematch.resilience")

# Prometheus metrics are imported lazily to avoid hard dependency
_metrics_available = False
_circuit_breaker_state = None
_circuit_breaker_open_count = None

F = TypeVar("F", bound=Callable[..., Any])


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def _init_metrics() -> None:
    """Initialize Prometheus metrics if available."""
    global _metrics_available, _circuit_breaker_state, _circuit_breaker_open_count

    if _metrics_available:
        return

    try:
        from prometheus_client import Gauge

        _circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
            ["service"],
        )
        _circuit_breaker_open_count = Gauge(
            "circuit_breaker_open",
            "Number of open circuit breakers",
        )
        _metrics_available = True
        logger.info("Prometheus metrics initialized for circuit breaker")
    except ImportError:
        logger.debug("prometheus-client not available; metrics disabled")
        _metrics_available = False


def _update_metrics(service: str, state: CircuitBreakerState) -> None:
    """Update Prometheus metrics for circuit breaker state change."""
    if not _metrics_available:
        _init_metrics()

    if not _metrics_available or _circuit_breaker_state is None:
        return

    try:
        state_value = {
            CircuitBreakerState.CLOSED: 0,
            CircuitBreakerState.OPEN: 1,
            CircuitBreakerState.HALF_OPEN: 2,
        }[state]
        _circuit_breaker_state.labels(service).set(state_value)

        if _circuit_breaker_open_count is not None:
            open_count = 1 if state == CircuitBreakerState.OPEN else 0
            _circuit_breaker_open_count.set(open_count)
    except Exception as e:
        logger.warning(f"Failed to update circuit breaker metrics: {e}")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is OPEN."""

    def __init__(self, service: str = "Claude API"):
        self.service = service
        msg = f"{service} circuit breaker is OPEN; request rejected to prevent cascading failure"
        super().__init__(msg)


class CircuitBreaker:
    """
    Circuit breaker for handling API failures with graceful degradation.

    This implementation uses the circuit breaker pattern to prevent cascading
    failures when calling external services (e.g., Claude API). The breaker
    tracks failure rates and automatically stops sending requests when the
    failure threshold is exceeded.

    Attributes:
        service_name: Name of the service being protected (for logging/metrics).
        failure_threshold: Failure percentage (0-100) before opening circuit.
        recovery_timeout: Seconds to wait before attempting recovery (HALF_OPEN).
        expected_exception: Exception type to catch for failures (default: LLMError).
    """

    def __init__(
        self,
        service_name: str = "Claude API",
        failure_threshold: int = 50,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = LLMError,
    ):
        """
        Initialize a CircuitBreaker.

        Args:
            service_name: Human-readable name of the protected service.
            failure_threshold: Failure percentage (0-100) before opening. Default: 50.
            recovery_timeout: Seconds to wait in OPEN state before trying HALF_OPEN.
                             Default: 60.
            expected_exception: Exception type to catch as failures. Default: LLMError.

        Raises:
            ValueError: If failure_threshold is not in range [0, 100].
        """
        if not (0 <= failure_threshold <= 100):
            raise ValueError(f"failure_threshold must be in [0, 100], got {failure_threshold}")

        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change_time = time.monotonic()

        logger.info(
            f"CircuitBreaker initialized for {service_name}: "
            f"threshold={failure_threshold}%, timeout={recovery_timeout}s"
        )

    # ─ Properties ────────────────────────────────────────────────────────

    @property
    def state(self) -> CircuitBreakerState:
        """Current state of the circuit breaker."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Number of consecutive failures."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Number of consecutive successes."""
        return self._success_count

    @property
    def is_closed(self) -> bool:
        """True if circuit is CLOSED (normal operation)."""
        return self._state == CircuitBreakerState.CLOSED

    @property
    def is_open(self) -> bool:
        """True if circuit is OPEN (fast-fail mode)."""
        return self._state == CircuitBreakerState.OPEN

    @property
    def is_half_open(self) -> bool:
        """True if circuit is HALF_OPEN (recovery test mode)."""
        return self._state == CircuitBreakerState.HALF_OPEN

    # ─ Core Methods ──────────────────────────────────────────────────────

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.

        If the circuit is OPEN, raises CircuitBreakerError immediately without
        calling the function. If HALF_OPEN, allows the call; on success, closes
        the circuit; on failure, reopens it.

        Args:
            func: Callable to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result of func(*args, **kwargs).

        Raises:
            CircuitBreakerError: If circuit is OPEN.
            expected_exception: If func raises the expected exception (when not OPEN).
        """
        if self.is_open:
            if self._on_timeout():
                logger.warning(
                    f"{self.service_name}: Recovery timeout elapsed; "
                    f"transitioning to HALF_OPEN"
                )
                self._transition_to(CircuitBreakerState.HALF_OPEN)
            else:
                raise CircuitBreakerError(self.service_name)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def __call__(self, func: F) -> F:
        """
        Decorator to wrap a function with circuit breaker protection.

        Usage:
            breaker = CircuitBreaker(service_name="Claude API")

            @breaker
            def call_claude(prompt: str) -> str:
                # Call Claude API
                ...

        Args:
            func: Function to decorate.

        Returns:
            Decorated function that applies circuit breaker.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper  # type: ignore

    # ─ State Transition Methods ──────────────────────────────────────────

    def _on_success(self) -> None:
        """
        Handle successful function execution.

        - If CLOSED: Reset counters.
        - If HALF_OPEN: Close circuit and reset counters.
        """
        self._success_count += 1

        if self.is_half_open:
            logger.warning(
                f"{self.service_name}: Recovery successful; "
                f"transitioning from HALF_OPEN to CLOSED"
            )
            self._transition_to(CircuitBreakerState.CLOSED)
        elif self.is_closed:
            # Reset failure count on success
            self._failure_count = 0

    def _on_failure(self) -> None:
        """
        Handle function execution failure.

        - Track consecutive failures.
        - If CLOSED and threshold exceeded: transition to OPEN.
        - If HALF_OPEN: transition to OPEN immediately.
        """
        self._failure_count += 1
        self._success_count = 0
        self._last_failure_time = time.monotonic()

        if self.is_half_open:
            logger.warning(
                f"{self.service_name}: Failure during recovery; "
                f"transitioning from HALF_OPEN to OPEN"
            )
            self._transition_to(CircuitBreakerState.OPEN)
        elif self.is_closed:
            failure_rate = self._calculate_failure_rate()
            if failure_rate >= self.failure_threshold:
                logger.warning(
                    f"{self.service_name}: Failure rate {failure_rate:.1f}% "
                    f"exceeds threshold {self.failure_threshold}%; "
                    f"opening circuit"
                )
                self._transition_to(CircuitBreakerState.OPEN)

    def _on_timeout(self) -> bool:
        """
        Check if recovery timeout has elapsed.

        Returns:
            True if circuit has been OPEN for >= recovery_timeout seconds.
        """
        if not self.is_open or self._last_failure_time is None:
            return False

        elapsed = time.monotonic() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    # ─ Helper Methods ────────────────────────────────────────────────────

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """
        Transition to a new state and update metrics.

        Args:
            new_state: Target state.
        """
        old_state = self._state
        self._state = new_state
        self._last_state_change_time = time.monotonic()

        # Reset counters on transition
        if new_state == CircuitBreakerState.CLOSED:
            self._failure_count = 0
            self._success_count = 0

        # Update Prometheus metrics
        _update_metrics(self.service_name, new_state)

        logger.warning(
            f"{self.service_name}: State transition {old_state.value} -> {new_state.value} "
            f"(failures={self._failure_count}, successes={self._success_count})"
        )

    def _calculate_failure_rate(self) -> float:
        """
        Calculate current failure rate as a percentage.

        Returns:
            Failure rate in range [0, 100].
        """
        total = self._failure_count + self._success_count
        if total == 0:
            return 0.0
        return (self._failure_count / total) * 100

    def reset(self) -> None:
        """
        Manually reset the circuit breaker to CLOSED state.

        Useful for testing or manual recovery intervention.
        """
        logger.warning(
            f"{self.service_name}: Manual reset from {self._state.value} to CLOSED"
        )
        self._transition_to(CircuitBreakerState.CLOSED)

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status of the circuit breaker.

        Returns:
            Dictionary with state, counters, and timing information.
        """
        return {
            "service": self.service_name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_rate_percent": self._calculate_failure_rate(),
            "failure_threshold_percent": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
            "last_state_change_time": self._last_state_change_time,
            "time_in_state_seconds": time.monotonic() - self._last_state_change_time,
        }
