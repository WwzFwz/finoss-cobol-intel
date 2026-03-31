"""Integration tests for the Phase 1 service pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

from cobol_intel.service import analyze_path

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
COPYBOOKS_DIR = REPO_ROOT / "copybooks"
RUNTIME_DIR = REPO_ROOT / "tests_runtime_artifacts"


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def test_analyze_path_writes_phase1_artifacts():
    result = analyze_path(
        SAMPLES_DIR,
        output_dir=RUNTIME_DIR,
        copybook_dirs=[COPYBOOKS_DIR],
    )

    manifest_path = result.run_dir / "manifest.json"
    assert manifest_path.exists()
    assert result.manifest.artifacts.ast
    assert result.manifest.artifacts.graphs
    assert result.manifest.artifacts.rules
    assert result.manifest.artifacts.docs

    call_graph_path = result.run_dir / "graphs" / "call_graph.json"
    summary_path = result.run_dir / "docs" / "summary.md"
    assert call_graph_path.exists()
    assert summary_path.exists()


def test_analyze_path_marks_successful_run_completed():
    result = analyze_path(
        SAMPLES_DIR,
        output_dir=RUNTIME_DIR,
        copybook_dirs=[COPYBOOKS_DIR],
    )

    assert result.manifest.is_success()
    assert result.manifest.errors == []
    assert len(result.parse_results) >= 10
