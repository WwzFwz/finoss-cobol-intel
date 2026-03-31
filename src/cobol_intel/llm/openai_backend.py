"""OpenAI API backend using the official OpenAI SDK."""

from __future__ import annotations

import os

from cobol_intel.llm.backend import LLMBackend, LLMResponse, retry_operation

_DEFAULT_MODEL = "gpt-5-mini"
_DEFAULT_MAX_OUTPUT_TOKENS = 4096
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_RETRIES = 2
_DEFAULT_RETRY_DELAY_SECONDS = 0.5


class OpenAIBackend(LLMBackend):
    """LLM backend using the OpenAI Responses API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds or float(
            os.environ.get("COBOL_INTEL_OPENAI_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS)
        )
        self._max_retries = max_retries if max_retries is not None else int(
            os.environ.get("COBOL_INTEL_OPENAI_MAX_RETRIES", _DEFAULT_MAX_RETRIES)
        )
        self._retry_delay_seconds = retry_delay_seconds
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self._api_key,
                timeout=self._timeout_seconds,
                max_retries=0,
            )
        return self._client

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_id(self) -> str:
        return self._model

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion using the OpenAI Responses API."""
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. "
                "Set it via environment variable or pass api_key to OpenAIBackend()."
            )

        client = self._get_client()
        kwargs: dict = {
            "model": self._model,
            "input": prompt,
            "max_output_tokens": self._max_output_tokens,
        }
        if system:
            kwargs["instructions"] = system
        kwargs["timeout"] = self._timeout_seconds
        response = retry_operation(
            lambda: client.responses.create(**kwargs),
            max_retries=self._max_retries,
            retry_delay_seconds=self._retry_delay_seconds,
        )
        usage = getattr(response, "usage", None)

        return LLMResponse(
            text=getattr(response, "output_text", ""),
            model=getattr(response, "model", self._model),
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
        )
