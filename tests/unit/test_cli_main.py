"""Unit tests for CLI backend resolution."""

from __future__ import annotations

import pytest

from cobol_intel.cli.main import _resolve_backend


def test_resolve_backend_supports_openai():
    backend = _resolve_backend("openai")

    assert backend.name == "openai"


def test_resolve_backend_rejects_unknown_name():
    with pytest.raises(Exception, match="claude, openai, ollama"):
        _resolve_backend("not-a-backend")
