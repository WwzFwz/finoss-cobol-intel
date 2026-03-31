"""Unit tests for the OpenAI backend without live API calls."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cobol_intel.llm.openai_backend import OpenAIBackend


def test_openai_backend_requires_api_key():
    backend = OpenAIBackend(api_key="")

    with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
        backend.generate("Explain this COBOL program")


def test_openai_backend_maps_response_fields():
    backend = OpenAIBackend(api_key="test-key", model="gpt-5-mini")

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "gpt-5-mini"
            assert kwargs["input"] == "Explain this COBOL program"
            assert kwargs["instructions"] == "You are a COBOL expert."
            return SimpleNamespace(
                output_text="This program validates balances.",
                model="gpt-5-mini",
                usage=SimpleNamespace(input_tokens=123, output_tokens=45),
            )

    backend._client = SimpleNamespace(responses=FakeResponses())

    response = backend.generate(
        "Explain this COBOL program",
        system="You are a COBOL expert.",
    )

    assert response.text == "This program validates balances."
    assert response.model == "gpt-5-mini"
    assert response.input_tokens == 123
    assert response.output_tokens == 45
