"""Unit tests for CLI backend resolution."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cobol_intel.cli.main import _resolve_backend, app


def test_resolve_backend_supports_openai():
    backend = _resolve_backend("openai")

    assert backend.name == "openai"


def test_resolve_backend_supports_local():
    class FakeLocalBackend:
        name = "local"

    import cobol_intel.llm.local_backend as local_backend

    original = local_backend.LocalBackend
    local_backend.LocalBackend = FakeLocalBackend
    try:
        backend = _resolve_backend("local")
    finally:
        local_backend.LocalBackend = original

    assert backend.name == "local"


def test_resolve_backend_rejects_unknown_name():
    with pytest.raises(Exception, match="claude, openai, ollama, local"):
        _resolve_backend("not-a-backend")


def test_explain_command_passes_parallel_and_cache_flags(monkeypatch):
    runner = CliRunner()
    captured: dict[str, object] = {}

    class FakeBackend:
        name = "openai"
        model_id = "gpt-5-mini"

    def fake_resolve_backend(model: str):
        assert model == "openai"
        return FakeBackend()

    def fake_explain_path(**kwargs):
        captured.update(kwargs)

        class _Status:
            value = "completed"

        class _Manifest:
            run_id = "run_001"
            status = _Status()

        class _Result:
            manifest = _Manifest()
            run_dir = "artifacts/demo/run_001"

        return _Result(), []

    monkeypatch.setattr("cobol_intel.cli.main._resolve_backend", fake_resolve_backend)
    monkeypatch.setattr("cobol_intel.service.explain.explain_path", fake_explain_path)

    result = runner.invoke(
        app,
        [
            "explain",
            "samples/complex/payment.cbl",
            "--model",
            "openai",
            "--parallel",
            "--max-workers",
            "2",
            "--no-cache",
        ],
    )

    assert result.exit_code == 0
    assert captured["parallel"] is True
    assert captured["max_workers"] == 2
    assert captured["use_cache"] is False
