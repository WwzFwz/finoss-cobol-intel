"""Abstract LLM backend interface and resilience helpers."""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar

_T = TypeVar("_T")


class RetryErrorKind(str, Enum):
    TIMEOUT = "timeout"
    TRANSIENT = "transient"
    PERMANENT = "permanent"


@dataclass(frozen=True)
class RetryEvent:
    attempt: int
    error_kind: RetryErrorKind
    error_message: str
    delay_seconds: float = 0.0


@dataclass
class LLMResponse:
    """Response from an LLM backend."""

    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    retry_count: int = 0
    timeout_count: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion from the LLM."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this backend (e.g. 'claude', 'ollama')."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Model identifier used by this backend."""
        ...

    def clone(self) -> LLMBackend:
        """Return a backend instance safe to use for another worker."""
        return self


def classify_retryable_error(exc: Exception) -> RetryErrorKind:
    """Classify backend exceptions into timeout, transient, or permanent."""
    if isinstance(exc, TimeoutError):
        return RetryErrorKind.TIMEOUT

    message = str(exc).lower()
    if any(token in message for token in {"timeout", "timed out", "deadline"}):
        return RetryErrorKind.TIMEOUT
    if any(
        token in message
        for token in {
            "temporary",
            "temporarily",
            "rate limit",
            "rate limited",
            "429",
            "connection reset",
            "connection aborted",
            "connection refused",
            "service unavailable",
            "try again",
            "unavailable",
        }
    ):
        return RetryErrorKind.TRANSIENT
    return RetryErrorKind.PERMANENT


def retry_operation(
    operation: Callable[[], _T],
    *,
    max_retries: int,
    retry_delay_seconds: float,
    backoff_multiplier: float = 2.0,
    jitter_ratio: float = 0.1,
    on_error: Callable[[RetryEvent], None] | None = None,
    on_retry: Callable[[RetryEvent], None] | None = None,
    classify_error: Callable[[Exception], RetryErrorKind] = classify_retryable_error,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> _T:
    """Run an operation with bounded retry, backoff, and lightweight telemetry."""
    attempts = max_retries + 1
    last_error: Exception | None = None
    current_delay = max(0.0, retry_delay_seconds)

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - exercised via backend tests
            last_error = exc
            error_kind = classify_error(exc)
            base_event = RetryEvent(
                attempt=attempt,
                error_kind=error_kind,
                error_message=str(exc),
            )
            if on_error is not None:
                on_error(base_event)

            is_retryable = error_kind in {
                RetryErrorKind.TIMEOUT,
                RetryErrorKind.TRANSIENT,
            }
            if attempt > max_retries or not is_retryable:
                break

            actual_delay = current_delay
            if actual_delay > 0 and jitter_ratio > 0:
                actual_delay += random.uniform(0.0, actual_delay * jitter_ratio)
            if on_retry is not None:
                on_retry(
                    RetryEvent(
                        attempt=attempt,
                        error_kind=error_kind,
                        error_message=str(exc),
                        delay_seconds=actual_delay,
                    )
                )
            if actual_delay > 0:
                sleep_fn(actual_delay)
            current_delay = current_delay * backoff_multiplier if current_delay > 0 else 0.0

    assert last_error is not None
    raise last_error
