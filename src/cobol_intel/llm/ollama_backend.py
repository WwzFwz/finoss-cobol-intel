"""Ollama local model backend for on-premise deployment."""

from __future__ import annotations

import os

from cobol_intel.llm.backend import LLMBackend, LLMResponse, retry_operation

_DEFAULT_MODEL = "llama3.1:8b"
_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_RETRIES = 2
_DEFAULT_RETRY_DELAY_SECONDS = 0.5
_DEFAULT_BACKOFF_MULTIPLIER = 2.0
_DEFAULT_JITTER_RATIO = 0.1


class OllamaBackend(LLMBackend):
    """LLM backend using a local Ollama instance."""

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        host: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS,
        backoff_multiplier: float = _DEFAULT_BACKOFF_MULTIPLIER,
        jitter_ratio: float = _DEFAULT_JITTER_RATIO,
    ) -> None:
        self._model = model
        self._host = host or os.environ.get("OLLAMA_HOST", _DEFAULT_HOST)
        self._timeout_seconds = timeout_seconds or float(
            os.environ.get("COBOL_INTEL_OLLAMA_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS)
        )
        self._max_retries = max_retries if max_retries is not None else int(
            os.environ.get("COBOL_INTEL_OLLAMA_MAX_RETRIES", _DEFAULT_MAX_RETRIES)
        )
        self._retry_delay_seconds = retry_delay_seconds
        self._backoff_multiplier = backoff_multiplier
        self._jitter_ratio = jitter_ratio
        self._client = None

    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self._host, timeout=self._timeout_seconds)
        return self._client

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model_id(self) -> str:
        return self._model

    def clone(self) -> OllamaBackend:
        return OllamaBackend(
            model=self._model,
            host=self._host,
            timeout_seconds=self._timeout_seconds,
            max_retries=self._max_retries,
            retry_delay_seconds=self._retry_delay_seconds,
            backoff_multiplier=self._backoff_multiplier,
            jitter_ratio=self._jitter_ratio,
        )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion using the local Ollama model."""
        client = self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
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
            lambda: client.chat(model=self._model, messages=messages),
            max_retries=self._max_retries,
            retry_delay_seconds=self._retry_delay_seconds,
            backoff_multiplier=self._backoff_multiplier,
            jitter_ratio=self._jitter_ratio,
            on_error=_on_error,
            on_retry=_on_retry,
        )

        text = response["message"]["content"]

        # Ollama provides token counts in eval_count / prompt_eval_count
        input_tokens = response.get("prompt_eval_count", 0)
        output_tokens = response.get("eval_count", 0)

        return LLMResponse(
            text=text,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retry_count=retry_count,
            timeout_count=timeout_count,
        )
