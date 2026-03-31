"""Unit tests for the change impact analyzer."""

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput
from cobol_intel.contracts.impact_output import ImpactType
from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.contracts.source_ref import SourceRef
from cobol_intel.analysis.impact_analyzer import analyze_impact


def _make_graph() -> CallGraphOutput:
    """A -> B -> C chain."""
    return CallGraphOutput(
        nodes=["A", "B", "C"],
        edges=[
            CallEdge(caller="A", callee="B", call_type="STATIC"),
            CallEdge(caller="B", callee="C", call_type="STATIC"),
        ],
        adjacency={"A": ["B"], "B": ["C"]},
        entry_points=["A"],
        external_calls=[],
    )


def _make_asts() -> dict[str, ASTOutput]:
    return {
        "A": ASTOutput(
            program_id="A", file_path="a.cbl", parser_name="antlr4",
            data_items=[DataItemOut(level=1, name="WS-BALANCE", pic="9(7)V99")],
            paragraphs=[ParagraphOut(name="MAIN", statements=[
                StatementOut(type="CALL", target="B"),
                StatementOut(type="MOVE", raw="MOVE WS-BALANCE TO WS-OUTPUT"),
            ])],
        ),
        "B": ASTOutput(
            program_id="B", file_path="b.cbl", parser_name="antlr4",
            data_items=[DataItemOut(level=1, name="WS-BALANCE", pic="9(7)V99")],
            paragraphs=[ParagraphOut(name="PROCESS", statements=[
                StatementOut(type="IF", condition="WS-BALANCE > 0"),
                StatementOut(type="CALL", target="C"),
            ])],
        ),
        "C": ASTOutput(
            program_id="C", file_path="c.cbl", parser_name="antlr4",
            paragraphs=[ParagraphOut(name="CALC", statements=[
                StatementOut(type="COMPUTE", raw="COMPUTE WS-TOTAL = WS-BALANCE * 1.1"),
            ])],
        ),
    }


def _make_rules() -> dict[str, RulesOutput]:
    return {
        "B": RulesOutput(
            program_id="B", file_path="b.cbl",
            rules=[BusinessRule(
                rule_id="R001", type="IF", condition="WS-BALANCE > 0",
                paragraph="PROCESS", actions=["CALL C"],
                source=SourceRef(file="b.cbl", paragraph="PROCESS"),
            )],
        ),
    }


def test_direct_caller_found():
    report = analyze_impact(
        changed_programs=["C"],
        changed_fields=[],
        call_graph=_make_graph(),
        asts_by_program=_make_asts(),
    )
    assert report.total_impacted >= 1
    direct = [e for e in report.impacted_entities if e.program_id == "B"]
    assert len(direct) == 1
    assert direct[0].impact_type == ImpactType.DIRECT_CALLER
    assert direct[0].distance == 1


def test_transitive_caller_found():
    report = analyze_impact(
        changed_programs=["C"],
        changed_fields=[],
        call_graph=_make_graph(),
        asts_by_program=_make_asts(),
    )
    transitive = [e for e in report.impacted_entities if e.program_id == "A"]
    assert len(transitive) == 1
    assert transitive[0].impact_type == ImpactType.TRANSITIVE_CALLER
    assert transitive[0].distance == 2


def test_field_reference_found():
    report = analyze_impact(
        changed_programs=[],
        changed_fields=["WS-BALANCE"],
        call_graph=_make_graph(),
        rules_by_program=_make_rules(),
        asts_by_program=_make_asts(),
    )
    impacted_ids = {e.program_id for e in report.impacted_entities}
    assert "A" in impacted_ids
    assert "B" in impacted_ids

    b_entity = next(e for e in report.impacted_entities if e.program_id == "B")
    assert "R001" in b_entity.affected_rules
    assert "PROCESS" in b_entity.affected_paragraphs


def test_max_depth_limits_traversal():
    report = analyze_impact(
        changed_programs=["C"],
        changed_fields=[],
        call_graph=_make_graph(),
        asts_by_program=_make_asts(),
        max_depth=1,
    )
    impacted_ids = {e.program_id for e in report.impacted_entities}
    assert "B" in impacted_ids
    assert "A" not in impacted_ids


def test_empty_input_returns_empty_report():
    report = analyze_impact(
        changed_programs=[],
        changed_fields=[],
        call_graph=CallGraphOutput(),
    )
    assert report.total_impacted == 0
