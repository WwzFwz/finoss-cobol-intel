"""Unit tests for API path traversal prevention."""

import shutil
from pathlib import Path

import pytest

from cobol_intel.api.errors import ApiError
from cobol_intel.api.security import safe_artifact_path

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "tests_runtime_api_security"


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def _fresh_run_dir() -> Path:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    run_dir = RUNTIME_DIR / "run_1"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def test_safe_path_allows_valid_artifact():
    run_dir = _fresh_run_dir()
    artifact = run_dir / "ast" / "program.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}")
    result = safe_artifact_path(run_dir, "ast/program.json")
    assert result == artifact.resolve()


def test_safe_path_blocks_traversal():
    run_dir = _fresh_run_dir()
    with pytest.raises(ApiError) as exc_info:
        safe_artifact_path(run_dir, "../../etc/passwd")
    assert exc_info.value.status_code == 400
    assert "traversal" in (exc_info.value.detail or "").lower()


def test_safe_path_blocks_dotdot_in_middle():
    run_dir = _fresh_run_dir()
    sub = run_dir / "ast"
    sub.mkdir()
    with pytest.raises(ApiError) as exc_info:
        safe_artifact_path(run_dir, "ast/../../etc/passwd")
    assert exc_info.value.status_code == 400


def test_safe_path_returns_404_for_missing_file():
    run_dir = _fresh_run_dir()
    with pytest.raises(ApiError) as exc_info:
        safe_artifact_path(run_dir, "nonexistent.json")
    assert exc_info.value.status_code == 404
