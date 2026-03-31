"""Unit tests for LLM context builder — no API calls required."""

from cobol_intel.contracts.ast_output import (
    ASTOutput,
    DataItemOut,
    ParagraphOut,
    StatementOut,
)
from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput
from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.llm.context_builder import (
    build_paragraph_prompt,
    build_program_prompt,
    build_system_prompt,
)


def _make_ast() -> ASTOutput:
    return ASTOutput(
        program_id="PAYMENT",
        file_path="payment.cbl",
        parser_name="antlr4",
        data_items=[
            DataItemOut(level=1, name="WS-AMOUNT", pic="9(9)V99", usage="COMP-3"),
            DataItemOut(
                level=1, name="WS-STATUS", pic="X(2)",
                children=[
                    DataItemOut(level=88, name="STATUS-OK", is_condition=True, condition_values=["00"]),
                ],
            ),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN-PROGRAM", statements=[
                StatementOut(type="PERFORM", target="VALIDATE"),
                StatementOut(type="IF", condition="STATUS-OK"),
                StatementOut(type="STOP-RUN"),
            ]),
            ParagraphOut(name="VALIDATE", statements=[
                StatementOut(type="CALL", target="DATEUTIL"),
                StatementOut(type="IF", condition="WS-DATE-VALID=\"N\""),
            ]),
        ],
    )


def _make_rules() -> RulesOutput:
    return RulesOutput(
        program_id="PAYMENT",
        rules=[
            BusinessRule(
                rule_id="R001", type="IF",
                condition="STATUS-OK",
                actions=["PERFORM", "PERFORM"],
                paragraph="MAIN-PROGRAM",
            ),
            BusinessRule(
                rule_id="R002", type="CONDITION-88",
                condition="STATUS-OK = 00",
            ),
        ],
    )


def _make_graph() -> CallGraphOutput:
    return CallGraphOutput(
        nodes=["PAYMENT", "DATEUTIL"],
        edges=[CallEdge(caller="PAYMENT", callee="DATEUTIL")],
        entry_points=["PAYMENT"],
        external_calls=["DATEUTIL"],
    )


class TestBuildSystemPrompt:
    def test_technical_mode_mentions_control_flow(self):
        prompt = build_system_prompt(ExplanationMode.TECHNICAL)
        assert "COBOL" in prompt
        assert "control flow" in prompt.lower() or "Control flow" in prompt

    def test_business_mode_mentions_business_logic(self):
        prompt = build_system_prompt(ExplanationMode.BUSINESS)
        assert "business" in prompt.lower()

    def test_audit_mode_mentions_compliance(self):
        prompt = build_system_prompt(ExplanationMode.AUDIT)
        assert "compliance" in prompt.lower() or "audit" in prompt.lower()

    def test_all_modes_produce_nonempty_prompts(self):
        for mode in ExplanationMode:
            prompt = build_system_prompt(mode)
            assert len(prompt) > 100


class TestBuildProgramPrompt:
    def test_contains_program_id(self):
        prompt = build_program_prompt(_make_ast())
        assert "PAYMENT" in prompt

    def test_contains_data_items(self):
        prompt = build_program_prompt(_make_ast())
        assert "WS-AMOUNT" in prompt
        assert "COMP-3" in prompt

    def test_contains_paragraphs(self):
        prompt = build_program_prompt(_make_ast())
        assert "MAIN-PROGRAM" in prompt
        assert "VALIDATE" in prompt

    def test_contains_rules_when_provided(self):
        prompt = build_program_prompt(_make_ast(), rules=_make_rules())
        assert "R001" in prompt
        assert "STATUS-OK" in prompt

    def test_contains_graph_when_provided(self):
        prompt = build_program_prompt(
            _make_ast(), call_graph=_make_graph(),
        )
        assert "DATEUTIL" in prompt
        assert "entry point" in prompt.lower()

    def test_truncates_when_over_budget(self):
        prompt = build_program_prompt(_make_ast(), max_context_chars=200)
        assert len(prompt) <= 400  # some overhead from truncation message
        assert "truncated" in prompt.lower()

    def test_truncation_preserves_rules_section_before_paragraphs(self):
        ast = _make_ast()
        ast.paragraphs = ast.paragraphs * 40
        prompt = build_program_prompt(ast, rules=_make_rules(), call_graph=_make_graph(), max_context_chars=800)
        assert "## Extracted Business Rules" in prompt
        assert "## Call Graph Context" in prompt


class TestBuildParagraphPrompt:
    def test_returns_prompt_for_existing_paragraph(self):
        prompt = build_paragraph_prompt(_make_ast(), "MAIN-PROGRAM")
        assert prompt is not None
        assert "MAIN-PROGRAM" in prompt
        assert "PERFORM" in prompt

    def test_returns_none_for_missing_paragraph(self):
        prompt = build_paragraph_prompt(_make_ast(), "NONEXISTENT")
        assert prompt is None

    def test_includes_relevant_rules(self):
        prompt = build_paragraph_prompt(
            _make_ast(), "MAIN-PROGRAM", rules=_make_rules(),
        )
        assert prompt is not None
        assert "R001" in prompt
