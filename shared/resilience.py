"""Reliability utilities — retry, circuit breaker, and timeout helpers.

Provides:
- retry: Decorator for automatic retry with exponential backoff.
- CircuitBreaker: Simple circuit breaker for external service calls.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("etl_project")

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first).
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function that retries on specified exceptions.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__} "
                            f"after error: {e}. Waiting {delay:.1f}s."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


class CircuitBreaker:
    """Simple circuit breaker for protecting external service calls.

    States:
    - CLOSED: Requests pass through normally.
    - OPEN: Requests fail fast without calling the protected function.
    - HALF_OPEN: A single request is allowed to test recovery.

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        result = breaker.call(external_function, *args, **kwargs)
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failure_count = 0
        self._state = self.CLOSED
        self._last_failure_time: float | None = None

    @property
    def state(self) -> str:
        if (
            self._state == self.OPEN
            and self._last_failure_time
            and (time.time() - self._last_failure_time >= self.recovery_timeout)
        ):
            self._state = self.HALF_OPEN
        return self._state

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Call func through the circuit breaker."""
        current_state = self.state
        if current_state == self.OPEN:
            raise RuntimeError("Circuit breaker is OPEN — failing fast")

        try:
            result = func(*args, **kwargs)
            if current_state == self.HALF_OPEN:
                self._reset()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = self.OPEN
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def _reset(self) -> None:
        self._failure_count = 0
        self._state = self.CLOSED
        self._last_failure_time = None
        logger.info("Circuit breaker reset to CLOSED")
