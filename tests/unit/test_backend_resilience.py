"""Unit tests for Claude and Ollama backend retry/timeout behavior."""

from __future__ import annotations

from types import SimpleNamespace

from cobol_intel.llm.claude_backend import ClaudeBackend
from cobol_intel.llm.ollama_backend import OllamaBackend


def test_claude_backend_retries_transient_failure():
    backend = ClaudeBackend(
        api_key="test-key",
        max_retries=1,
        retry_delay_seconds=0,
        timeout_seconds=9.0,
    )

    class TextBlock:
        type = "text"
        text = "Recovered Claude response."

    class FakeMessages:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            assert kwargs["timeout"] == 9.0
            if self.calls == 1:
                raise RuntimeError("temporary claude failure")
            return SimpleNamespace(
                model="claude-sonnet-4-20250514",
                content=[TextBlock()],
                usage=SimpleNamespace(input_tokens=11, output_tokens=6),
            )

    fake = FakeMessages()
    backend._client = SimpleNamespace(messages=fake)

    response = backend.generate("Explain this COBOL program")

    assert fake.calls == 2
    assert response.text == "Recovered Claude response."
    assert response.retry_count == 1
    assert response.timeout_count == 0


def test_ollama_backend_retries_transient_failure():
    backend = OllamaBackend(
        max_retries=1,
        retry_delay_seconds=0,
        timeout_seconds=8.0,
    )

    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def chat(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary ollama failure")
            return {
                "message": {"content": "Recovered Ollama response."},
                "prompt_eval_count": 12,
                "eval_count": 7,
            }

    fake = FakeClient()
    backend._client = fake

    response = backend.generate("Explain this COBOL program")

    assert fake.calls == 2
    assert response.text == "Recovered Ollama response."
    assert response.retry_count == 1
    assert response.timeout_count == 0
