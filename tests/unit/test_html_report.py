"""Unit tests for the HTML report generator."""

from datetime import datetime, timezone

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput
from cobol_intel.contracts.manifest import Manifest, RunStatus
from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.contracts.source_ref import SourceRef
from cobol_intel.outputs.doc_generator import generate_program_doc
from cobol_intel.outputs.html_report import render_html_report


def _make_docs():
    ast_a = ASTOutput(
        program_id="PAYMENT", file_path="payment.cbl", parser_name="antlr4",
        data_items=[DataItemOut(level=1, name="WS-AMOUNT", pic="9(7)V99")],
        paragraphs=[ParagraphOut(name="PROCESS-PAYMENT", statements=[
            StatementOut(type="CALL", target="ACCTVAL"),
            StatementOut(type="MOVE", raw="MOVE WS-AMOUNT TO WS-OUTPUT"),
        ])],
    )
    ast_b = ASTOutput(
        program_id="ACCTVAL", file_path="acctval.cbl", parser_name="antlr4",
        paragraphs=[ParagraphOut(name="VALIDATE", statements=[
            StatementOut(type="IF", condition="WS-STATUS = 'ACTIVE'"),
        ])],
    )
    rules = RulesOutput(
        program_id="ACCTVAL", file_path="acctval.cbl",
        rules=[BusinessRule(
            rule_id="R001", type="IF", condition="WS-STATUS = 'ACTIVE'",
            paragraph="VALIDATE", actions=["CONTINUE"],
            source=SourceRef(file="acctval.cbl", paragraph="VALIDATE"),
        )],
    )
    call_graph = CallGraphOutput(
        nodes=["PAYMENT", "ACCTVAL"],
        edges=[CallEdge(caller="PAYMENT", callee="ACCTVAL", call_type="STATIC")],
        adjacency={"PAYMENT": ["ACCTVAL"]},
        entry_points=["PAYMENT"],
        external_calls=[],
    )
    doc_a = generate_program_doc(ast_a, call_graph=call_graph)
    doc_b = generate_program_doc(ast_b, rules=rules, call_graph=call_graph)
    return [doc_a, doc_b], call_graph


def _make_manifest(name: str = "test-project"):
    return Manifest(
        tool_version="0.2.0-dev", run_id="test-run-001",
        project_name=name, status=RunStatus.COMPLETED,
        started_at=datetime.now(timezone.utc), input_paths=["test/"],
    )


def test_html_report_is_valid_html():
    docs, graph = _make_docs()
    html = render_html_report(_make_manifest(), docs, graph)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "<title>" in html


def test_html_report_contains_programs():
    docs, graph = _make_docs()
    html = render_html_report(_make_manifest(), docs, graph)
    assert "PAYMENT" in html
    assert "ACCTVAL" in html


def test_html_report_has_sidebar_nav():
    docs, graph = _make_docs()
    html = render_html_report(_make_manifest(), docs, graph)
    assert 'class="sidebar"' in html
    assert 'id="search"' in html
    assert "filterPrograms" in html


def test_html_report_has_mermaid():
    docs, graph = _make_docs()
    html = render_html_report(_make_manifest(), docs, graph)
    assert "mermaid" in html
    assert "PAYMENT" in html


def test_html_report_has_embedded_css():
    docs, graph = _make_docs()
    html = render_html_report(_make_manifest(), docs, graph)
    assert "<style>" in html
    assert "font-family" in html


def test_html_report_no_graph():
    docs, _ = _make_docs()
    html = render_html_report(_make_manifest(), docs, call_graph=None)
    assert "<!DOCTYPE html>" in html
    assert "PAYMENT" in html


def test_html_report_escapes_special_chars():
    docs, graph = _make_docs()
    manifest = _make_manifest("test<script>alert(1)</script>")
    html = render_html_report(manifest, docs, graph)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
