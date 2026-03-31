"""Unit tests for the documentation generator."""

import shutil
from pathlib import Path

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput
from cobol_intel.contracts.manifest import Manifest, RunStatus
from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.contracts.source_ref import SourceRef
from cobol_intel.outputs.doc_generator import generate_program_doc, generate_project_report
from cobol_intel.service.doc_service import generate_docs
from cobol_intel.service.pipeline import analyze_path

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
RUNTIME_DIR = REPO_ROOT / "tests_runtime_docs"


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def _make_ast() -> ASTOutput:
    return ASTOutput(
        program_id="TESTPROG",
        file_path="test.cbl",
        parser_name="antlr4",
        data_items=[
            DataItemOut(level=1, name="WS-RECORD"),
            DataItemOut(level=5, name="WS-AMOUNT", pic="9(7)V99", usage="COMP-3"),
        ],
        paragraphs=[
            ParagraphOut(
                name="MAIN-LOGIC",
                statements=[
                    StatementOut(type="IF", condition="WS-AMOUNT > 0"),
                    StatementOut(type="PERFORM", target="CALC-TOTAL"),
                ],
            ),
        ],
    )


def _make_rules() -> RulesOutput:
    return RulesOutput(
        program_id="TESTPROG",
        file_path="test.cbl",
        rules=[
            BusinessRule(
                rule_id="R001",
                type="IF",
                condition="WS-AMOUNT > 0",
                paragraph="MAIN-LOGIC",
                actions=["PERFORM CALC-TOTAL"],
                source=SourceRef(file="test.cbl", paragraph="MAIN-LOGIC"),
            ),
        ],
    )


def _make_graph() -> CallGraphOutput:
    return CallGraphOutput(
        nodes=["TESTPROG", "SUBPROG"],
        edges=[CallEdge(caller="TESTPROG", callee="SUBPROG", call_type="STATIC")],
        adjacency={"TESTPROG": ["SUBPROG"]},
        entry_points=["TESTPROG"],
        external_calls=[],
    )


def test_generate_program_doc_has_all_sections():
    doc = generate_program_doc(_make_ast(), _make_rules(), _make_graph())
    assert "# TESTPROG" in doc.markdown
    assert "## Data Dictionary" in doc.markdown
    assert "## Procedure Flow" in doc.markdown
    assert "## Business Rules" in doc.markdown
    assert "## Call Dependencies" in doc.markdown
    assert "WS-AMOUNT" in doc.markdown
    assert "COMP-3" in doc.markdown


def test_generate_program_doc_without_optional_data():
    ast = ASTOutput(program_id="MINIMAL", file_path="min.cbl", parser_name="antlr4")
    doc = generate_program_doc(ast)
    assert "# MINIMAL" in doc.markdown
    assert "No data items" in doc.markdown


def test_generate_project_report():
    manifest = Manifest(
        tool_version="0.1.0",
        run_id="run_001",
        project_name="demo",
        status=RunStatus.COMPLETED,
        started_at="2026-04-01T00:00:00Z",
        input_paths=["samples/"],
    )
    doc = generate_program_doc(_make_ast(), _make_rules(), _make_graph())
    report = generate_project_report(manifest, [doc], _make_graph())
    assert "# Project Report: demo" in report
    assert "## Program Inventory" in report
    assert "TESTPROG" in report
    assert "```mermaid" in report


def test_generate_docs_service_from_real_run():
    result = analyze_path(
        path=SAMPLES_DIR / "complex" / "payment.cbl",
        output_dir=str(RUNTIME_DIR),
    )
    generated = generate_docs(result.run_dir)
    assert len(generated) >= 2  # at least 1 program doc + 1 project report
    for path in generated:
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert len(content) > 50
