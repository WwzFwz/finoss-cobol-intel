"""Unit tests for the local fine-tuned model backend."""

from __future__ import annotations

import pytest

from cobol_intel.llm.local_backend import LocalBackend


def test_local_backend_requires_model_path():
    with pytest.raises(ValueError, match="Model path required"):
        LocalBackend(model_path="")


def test_local_backend_name_and_model_id():
    backend = LocalBackend(model_path="/tmp/fake-model")
    assert backend.name == "local"
    assert backend.model_id == "/tmp/fake-model"
    assert backend._do_sample is False


def test_local_backend_from_env(monkeypatch):
    monkeypatch.setenv("COBOL_INTEL_LOCAL_MODEL_PATH", "/models/cobol-7b")
    monkeypatch.setenv("COBOL_INTEL_LOCAL_DO_SAMPLE", "true")
    monkeypatch.setenv("COBOL_INTEL_LOCAL_TEMPERATURE", "0.2")
    monkeypatch.setenv("COBOL_INTEL_LOCAL_TOP_P", "0.8")
    monkeypatch.setenv("COBOL_INTEL_LOCAL_REPETITION_PENALTY", "1.05")
    backend = LocalBackend()
    assert backend.model_id == "/models/cobol-7b"
    assert backend._do_sample is True
    assert backend._temperature == 0.2
    assert backend._top_p == 0.8
    assert backend._repetition_penalty == 1.05


def test_local_backend_generate_raises_without_torch():
    backend = LocalBackend(model_path="/tmp/fake-model")
    # generate() will fail because torch/transformers aren't installed
    # in the test environment (and the model path doesn't exist),
    # but we verify it reaches the loading stage
    with pytest.raises((ImportError, OSError)):
        backend.generate("Explain this program")
