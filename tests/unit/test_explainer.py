"""Unit tests for explanation engine using a mock LLM backend."""

from cobol_intel.contracts.ast_output import ASTOutput, ParagraphOut, StatementOut
from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.llm.backend import LLMBackend, LLMResponse
from cobol_intel.llm.explainer import explain_program


class MockBackend(LLMBackend):
    """Deterministic mock backend for testing without API calls."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model_id(self) -> str:
        return "mock-v1"

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        self.calls.append(prompt[:80])
        return LLMResponse(
            text=(
                "## Program Summary\n"
                "This program processes payments.\n\n"
                "## Data Structures\n"
                "WS-AMOUNT stores the payment amount.\n\n"
                "## Business Rules\n"
                "Payment is processed only when status is OK."
            ),
            model="mock-v1",
            input_tokens=100,
            output_tokens=50,
        )


def _make_ast() -> ASTOutput:
    return ASTOutput(
        program_id="PAYMENT",
        file_path="payment.cbl",
        parser_name="antlr4",
        paragraphs=[
            ParagraphOut(name="MAIN-PROGRAM", statements=[
                StatementOut(type="PERFORM", target="VALIDATE"),
                StatementOut(type="STOP-RUN"),
            ]),
            ParagraphOut(name="VALIDATE", statements=[
                StatementOut(type="CALL", target="DATEUTIL"),
            ]),
        ],
    )


def _make_rules() -> RulesOutput:
    return RulesOutput(
        program_id="PAYMENT",
        rules=[
            BusinessRule(
                rule_id="R001",
                type="IF",
                condition="STATUS-OK",
                paragraph="MAIN-PROGRAM",
            ),
        ],
    )


class TestExplainProgram:
    def test_returns_explanation_output(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast())
        assert result.program_id == "PAYMENT"
        assert result.backend == "mock"
        assert result.model == "mock-v1"
        assert result.mode == ExplanationMode.TECHNICAL

    def test_calls_backend_for_summary_and_each_paragraph(self):
        backend = MockBackend()
        ast = _make_ast()
        explain_program(backend, ast)
        # 1 summary call + 2 paragraph calls
        assert len(backend.calls) == 3

    def test_parses_summary_sections(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast())
        assert "processes payments" in result.program_summary
        assert "WS-AMOUNT" in result.data_summary
        assert "status is OK" in result.business_rules_summary

    def test_paragraph_explanations_have_source_refs(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast())
        assert len(result.paragraph_explanations) == 2
        for para_exp in result.paragraph_explanations:
            assert para_exp.source is not None
            assert para_exp.source.file == "payment.cbl"

    def test_top_level_summaries_have_traceability(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast(), rules=_make_rules())
        assert result.program_summary_sources
        assert result.data_summary_sources
        assert result.business_rules_summary_sources
        assert result.program_summary_sources[0].file == "payment.cbl"

    def test_tokens_are_accumulated(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast())
        # 3 calls * 150 tokens each = 450
        assert result.tokens_used == 450

    def test_business_mode(self):
        backend = MockBackend()
        result = explain_program(
            backend, _make_ast(), mode=ExplanationMode.BUSINESS,
        )
        assert result.mode == ExplanationMode.BUSINESS

    def test_with_rules(self):
        backend = MockBackend()
        result = explain_program(backend, _make_ast(), rules=_make_rules())
        assert result.program_id == "PAYMENT"
        # Should still work with rules context
        assert len(result.paragraph_explanations) == 2

    def test_limits_number_of_paragraph_calls(self):
        backend = MockBackend()
        ast = _make_ast()
        ast.paragraphs.extend(
            ParagraphOut(name=f"EXTRA-{idx}", statements=[StatementOut(type="DISPLAY")])
            for idx in range(10)
        )
        result = explain_program(backend, ast, max_paragraph_explanations=3)
        assert len(backend.calls) == 4
        assert result.paragraph_limit == 3
        assert result.paragraphs_skipped
