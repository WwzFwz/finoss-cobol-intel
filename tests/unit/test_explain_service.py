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


class CountingOpenAIBackend(LLMBackend):
    def __init__(self) -> None:
        self.calls = 0

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_id(self) -> str:
        return "gpt-5-mini"

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            text=(
                "## Program Summary\nSummary.\n\n"
                "## Data Structures\nData.\n\n"
                "## Business Rules\nRules."
            ),
            model="gpt-5-mini",
            input_tokens=80,
            output_tokens=40,
        )


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


def test_explain_path_strict_policy_blocks_sensitive_cloud_backend():
    backend = CountingOpenAIBackend()
    run_result, explanations = explain_path(
        path=SAMPLES_DIR / "with_copybook" / "replacing_customer.cbl",
        backend=backend,
        mode=ExplanationMode.TECHNICAL,
        output_dir=RUNTIME_DIR,
        strict_policy=True,
    )

    assert explanations == []
    assert backend.calls == 0
    assert any(error.module == "policy" for error in run_result.manifest.errors)


def test_explain_path_stops_when_token_budget_is_reached():
    backend = CountingOpenAIBackend()
    run_result, explanations = explain_path(
        path=SAMPLES_DIR / "complex",
        backend=backend,
        mode=ExplanationMode.TECHNICAL,
        output_dir=RUNTIME_DIR,
        max_tokens_per_run=200,
    )

    assert explanations
    assert len(explanations) < len([result for result in run_result.parse_results if result.success])
    assert run_result.manifest.governance.budget_exhausted is True
    assert any("Token budget" in warning for warning in run_result.manifest.warnings)
