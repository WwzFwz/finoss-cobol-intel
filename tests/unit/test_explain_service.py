"""Unit tests for the LLM explanation service layer."""

from __future__ import annotations

import shutil
from pathlib import Path

from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.llm.backend import LLMBackend, LLMResponse
from cobol_intel.service.explain import explain_path

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
RUNTIME_DIR = REPO_ROOT / "tests_runtime_artifacts"


class AlwaysFailBackend(LLMBackend):
    @property
    def name(self) -> str:
        return "fail"

    @property
    def model_id(self) -> str:
        return "fail-v1"

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        raise RuntimeError("backend unavailable")


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def test_explain_path_records_partial_failure_in_manifest():
    run_result, explanations = explain_path(
        path=SAMPLES_DIR / "complex" / "payment.cbl",
        backend=AlwaysFailBackend(),
        mode=ExplanationMode.TECHNICAL,
        output_dir=RUNTIME_DIR,
    )

    assert explanations == []
    assert run_result.manifest.status.value == "partially_completed"
    assert run_result.manifest.errors
    assert any(error.module == "llm" for error in run_result.manifest.errors)
    assert (run_result.run_dir / "manifest.json").exists()
    assert (run_result.run_dir / "logs" / "audit_events.jsonl").exists()
