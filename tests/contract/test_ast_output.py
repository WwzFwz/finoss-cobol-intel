"""Contract tests for AST output schema."""

from cobol_intel.contracts.ast_output import (
    ASTOutput,
    DataItemOut,
    ParagraphOut,
    StatementOut,
)
from cobol_intel.contracts.source_ref import SourceRef


def test_ast_output_schema_version():
    ast = ASTOutput(program_id="HELLO")
    assert ast.schema_version == "1.0"


def test_ast_output_serializes_with_required_fields():
    ast = ASTOutput(program_id="HELLO", parser_name="antlr4")
    data = ast.model_dump()
    required = {"schema_version", "program_id", "file_path", "parser_name",
                "data_items", "paragraphs", "copybooks_used"}
    assert required.issubset(data.keys())


def test_ast_output_nested_data_items():
    child = DataItemOut(level=5, name="CHILD-FIELD", pic="X(10)")
    parent = DataItemOut(level=1, name="PARENT-GROUP", children=[child])
    ast = ASTOutput(program_id="TEST", data_items=[parent])

    data = ast.model_dump()
    assert len(data["data_items"]) == 1
    assert len(data["data_items"][0]["children"]) == 1
    assert data["data_items"][0]["children"][0]["name"] == "CHILD-FIELD"


def test_ast_output_paragraphs_with_statements():
    stmt = StatementOut(type="DISPLAY", raw='DISPLAY "HELLO"', target="SCREEN", condition=None)
    para = ParagraphOut(name="MAIN-PROGRAM", statements=[stmt])
    ast = ASTOutput(program_id="TEST", paragraphs=[para])

    data = ast.model_dump()
    assert data["paragraphs"][0]["statements"][0]["type"] == "DISPLAY"
    assert data["paragraphs"][0]["statements"][0]["raw"] == 'DISPLAY "HELLO"'
    assert data["paragraphs"][0]["statements"][0]["target"] == "SCREEN"


def test_ast_output_condition_item():
    cond = DataItemOut(
        level=88, name="ACCT-ACTIVE", is_condition=True,
        condition_values=["Y"],
    )
    parent = DataItemOut(level=5, name="ACCT-STATUS", pic="X", children=[cond])
    ast = ASTOutput(data_items=[parent])

    data = ast.model_dump()
    child = data["data_items"][0]["children"][0]
    assert child["is_condition"] is True
    assert child["condition_values"] == ["Y"]


def test_ast_output_with_source_ref():
    ref = SourceRef(file="CALC.cbl", paragraph="MAIN", lines=(10, 20))
    stmt = StatementOut(type="COMPUTE", source=ref)
    ast = ASTOutput(paragraphs=[ParagraphOut(name="MAIN", statements=[stmt])])

    data = ast.model_dump()
    source = data["paragraphs"][0]["statements"][0]["source"]
    assert source["file"] == "CALC.cbl"
    assert list(source["lines"]) == [10, 20]


def test_ast_output_empty_program():
    ast = ASTOutput()
    assert ast.program_id is None
    assert ast.data_items == []
    assert ast.paragraphs == []
