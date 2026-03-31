"""Abstract LLM backend interface.

All LLM backends (Claude, OpenAI, Ollama, local) must implement this interface.
See ADR-003 in docs/DECISIONS.md.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, TypeVar

_T = TypeVar("_T")


@dataclass
class LLMResponse:
    """Response from an LLM backend."""

    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt / main content.
            system: Optional system prompt for context setting.

        Returns:
            LLMResponse with generated text and token usage.
        """
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


def retry_operation(
    operation: Callable[[], _T],
    *,
    max_retries: int,
    retry_delay_seconds: float,
) -> _T:
    """Run an operation with a small bounded retry loop."""
    attempts = max_retries + 1
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - exercised through backend tests
            last_error = exc
            if attempt >= max_retries:
                break
            if retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)

    assert last_error is not None
    raise last_error
