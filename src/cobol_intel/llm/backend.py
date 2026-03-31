"""Abstract LLM backend interface.

All LLM backends (Claude, OpenAI, Ollama, local) must implement this interface.
See ADR-003 in docs/DECISIONS.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


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
