"""Claude API backend using Anthropic SDK."""

from __future__ import annotations

import os

from cobol_intel.llm.backend import LLMBackend, LLMResponse, retry_operation

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_RETRIES = 2
_DEFAULT_RETRY_DELAY_SECONDS = 0.5
_DEFAULT_BACKOFF_MULTIPLIER = 2.0
_DEFAULT_JITTER_RATIO = 0.1


class ClaudeBackend(LLMBackend):
    """LLM backend using the Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS,
        backoff_multiplier: float = _DEFAULT_BACKOFF_MULTIPLIER,
        jitter_ratio: float = _DEFAULT_JITTER_RATIO,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._max_tokens = max_tokens
        self._timeout_seconds = timeout_seconds or float(
            os.environ.get("COBOL_INTEL_CLAUDE_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS)
        )
        self._max_retries = max_retries if max_retries is not None else int(
            os.environ.get("COBOL_INTEL_CLAUDE_MAX_RETRIES", _DEFAULT_MAX_RETRIES)
        )
        self._retry_delay_seconds = retry_delay_seconds
        self._backoff_multiplier = backoff_multiplier
        self._jitter_ratio = jitter_ratio
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self._api_key,
                timeout=self._timeout_seconds,
                max_retries=0,
            )
        return self._client

    @property
    def name(self) -> str:
        return "claude"

    @property
    def model_id(self) -> str:
        return self._model

    def clone(self) -> ClaudeBackend:
        return ClaudeBackend(
            api_key=self._api_key,
            model=self._model,
            max_tokens=self._max_tokens,
            timeout_seconds=self._timeout_seconds,
            max_retries=self._max_retries,
            retry_delay_seconds=self._retry_delay_seconds,
            backoff_multiplier=self._backoff_multiplier,
            jitter_ratio=self._jitter_ratio,
        )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion using the Claude API."""
        if not self._api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Set it via environment variable or pass api_key to ClaudeBackend()."
            )

        client = self._get_client()
        kwargs: dict = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        kwargs["timeout"] = self._timeout_seconds
        retry_count = 0
        timeout_count = 0

        def _on_error(event) -> None:
            nonlocal timeout_count
            if event.error_kind.value == "timeout":
                timeout_count += 1

        def _on_retry(event) -> None:
            nonlocal retry_count
            retry_count += 1

        response = retry_operation(
            lambda: client.messages.create(**kwargs),
            max_retries=self._max_retries,
            retry_delay_seconds=self._retry_delay_seconds,
            backoff_multiplier=self._backoff_multiplier,
            jitter_ratio=self._jitter_ratio,
            on_error=_on_error,
            on_retry=_on_retry,
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return LLMResponse(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            retry_count=retry_count,
            timeout_count=timeout_count,
        )
