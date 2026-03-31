"""Claude API backend using Anthropic SDK."""

from __future__ import annotations

import os

from cobol_intel.llm.backend import LLMBackend, LLMResponse

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 4096


class ClaudeBackend(LLMBackend):
    """LLM backend using the Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    @property
    def name(self) -> str:
        return "claude"

    @property
    def model_id(self) -> str:
        return self._model

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

        response = client.messages.create(**kwargs)

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return LLMResponse(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
