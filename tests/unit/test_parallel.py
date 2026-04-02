"""Unit tests for parallel LLM processing."""

from __future__ import annotations

from cobol_intel.contracts.ast_output import ASTOutput, ParagraphOut, StatementOut
from cobol_intel.llm.backend import LLMBackend, LLMResponse
from cobol_intel.service.parallel import (
    _DEFAULT_WORKERS,
    ExplainJob,
    parallel_explain,
)


def _make_ast(program_id: str) -> ASTOutput:
    return ASTOutput(
        program_id=program_id,
        file_path=f"{program_id.lower()}.cbl",
        parser_name="antlr4",
        paragraphs=[
            ParagraphOut(
                name="MAIN",
                statements=[StatementOut(type="DISPLAY", raw="DISPLAY 'HELLO'")],
            )
        ],
    )


class FakeBackend(LLMBackend):
    def __init__(self, name: str = "openai", fail_program: str | None = None) -> None:
        self._name = name
        self._model_id = "gpt-4o"
        self.fail_program = fail_program
        self.clone_calls = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def model_id(self) -> str:
        return self._model_id

    def clone(self) -> LLMBackend:
        self.clone_calls += 1
        return FakeBackend(name=self._name, fail_program=self.fail_program)

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        if self.fail_program and self.fail_program in prompt:
            raise RuntimeError("Rate limited")
        return LLMResponse(
            text=(
                "## Program Summary\nTest summary\n"
                "## Data Structures\nNone\n"
                "## Business Rules\nNone"
            ),
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )


def _job(program_id: str) -> ExplainJob:
    return ExplainJob(index=int(program_id.replace("PROG", "") or 0), ast=_make_ast(program_id))


def test_parallel_explain_empty():
    results = parallel_explain([], FakeBackend())
    assert results == []


def test_parallel_explain_single():
    results = parallel_explain([_job("PROG1")], FakeBackend())
    assert len(results) == 1
    assert results[0].explanation is not None
    assert results[0].error is None


def test_parallel_explain_multiple():
    jobs = [_job(f"PROG{i}") for i in range(3)]
    results = parallel_explain(jobs, FakeBackend())
    assert len(results) == 3
    assert all(r.explanation is not None for r in results)


def test_parallel_explain_preserves_order():
    jobs = [_job(f"PROG{i}") for i in range(5)]
    results = parallel_explain(jobs, FakeBackend())
    for i, result in enumerate(results):
        assert result.index == i


def test_parallel_explain_handles_error():
    jobs = [_job("PROG0"), _job("PROG1")]
    results = parallel_explain(jobs, FakeBackend(fail_program="PROG1"), max_workers=1)
    assert len(results) == 2
    assert results[0].explanation is not None
    assert results[1].error is not None


def test_parallel_explain_clones_backend_per_job():
    backend = FakeBackend()
    jobs = [_job("PROG0"), _job("PROG1")]
    results = parallel_explain(jobs, backend, max_workers=2)
    assert len(results) == 2
    assert backend.clone_calls == len(jobs)


def test_default_workers_per_backend():
    assert _DEFAULT_WORKERS["claude"] == 4
    assert _DEFAULT_WORKERS["openai"] == 8
    assert _DEFAULT_WORKERS["ollama"] == 1
    assert _DEFAULT_WORKERS["local"] == 1
