"""Unit tests for parallel LLM processing."""

from unittest.mock import MagicMock

from cobol_intel.contracts.ast_output import ASTOutput, ParagraphOut, StatementOut
from cobol_intel.llm.backend import LLMResponse
from cobol_intel.service.parallel import _DEFAULT_WORKERS, parallel_explain


def _make_ast(program_id: str) -> ASTOutput:
    return ASTOutput(
        program_id=program_id, file_path=f"{program_id.lower()}.cbl", parser_name="antlr4",
        paragraphs=[ParagraphOut(name="MAIN", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'HELLO'"),
        ])],
    )


def _mock_backend(name: str = "openai") -> MagicMock:
    backend = MagicMock()
    backend.name = name
    backend.model_id = "gpt-4o"
    backend.generate.return_value = LLMResponse(
        text="## Program Summary\nTest summary\n## Data Structures\nNone\n## Business Rules\nNone",
        model="gpt-4o", input_tokens=100, output_tokens=50,
    )
    return backend


def test_parallel_explain_empty():
    results = parallel_explain([], _mock_backend())
    assert results == []


def test_parallel_explain_single():
    ast = _make_ast("PROG1")
    results = parallel_explain([(ast, None)], _mock_backend())
    assert len(results) == 1
    assert results[0].explanation is not None
    assert results[0].error is None


def test_parallel_explain_multiple():
    programs = [(_make_ast(f"PROG{i}"), None) for i in range(3)]
    results = parallel_explain(programs, _mock_backend())
    assert len(results) == 3
    for r in results:
        assert r.explanation is not None


def test_parallel_explain_preserves_order():
    programs = [(_make_ast(f"PROG{i}"), None) for i in range(5)]
    results = parallel_explain(programs, _mock_backend())
    for i, r in enumerate(results):
        assert r.index == i


def test_parallel_explain_handles_error():
    backend = _mock_backend()
    call_count = 0
    ok_response = LLMResponse(
        text="## Program Summary\nOK\n## Data Structures\n\n## Business Rules\n",
        model="gpt-4o", input_tokens=10, output_tokens=5,
    )

    def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # First program succeeds (needs 2 generate calls: summary + 1 paragraph)
        if call_count <= 2:
            return ok_response
        # Second program fails on first generate call
        raise RuntimeError("Rate limited")

    backend.generate.side_effect = _side_effect
    programs = [(_make_ast("OK"), None), (_make_ast("FAIL"), None)]
    results = parallel_explain(programs, backend, max_workers=1)
    assert len(results) == 2
    successes = [r for r in results if r.explanation is not None]
    failures = [r for r in results if r.error is not None]
    assert len(successes) == 1
    assert len(failures) == 1


def test_default_workers_per_backend():
    assert _DEFAULT_WORKERS["claude"] == 4
    assert _DEFAULT_WORKERS["openai"] == 8
    assert _DEFAULT_WORKERS["ollama"] == 1


def test_custom_max_workers():
    programs = [(_make_ast(f"PROG{i}"), None) for i in range(2)]
    results = parallel_explain(programs, _mock_backend(), max_workers=1)
    assert len(results) == 2
    assert all(r.explanation is not None for r in results)
