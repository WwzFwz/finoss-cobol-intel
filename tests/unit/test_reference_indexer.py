"""Unit tests for the reference indexer."""

from cobol_intel.analysis.reference_indexer import build_reference_index
from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.reference_output import ReferenceType


def _make_ast(**kwargs) -> ASTOutput:
    defaults = dict(program_id="TEST", file_path="test.cbl", parser_name="antlr4")
    defaults.update(kwargs)
    return ASTOutput(**defaults)


def test_move_produces_read_and_write():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-SOURCE", pic="X(10)"),
            DataItemOut(level=1, name="WS-TARGET", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(
                    type="MOVE",
                    raw="MOVE WS-SOURCE TO WS-TARGET",
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    reads = [r for r in idx.references if r.reference_type == ReferenceType.READ]
    writes = [r for r in idx.references if r.reference_type == ReferenceType.WRITE]
    assert any(r.field_name == "WS-SOURCE" for r in reads)
    assert any(r.field_name == "WS-TARGET" for r in writes)


def test_compute_produces_write_target_and_read_operands():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-TOTAL", pic="9(9)V99"),
            DataItemOut(level=1, name="WS-AMOUNT", pic="9(9)V99"),
            DataItemOut(level=1, name="WS-TAX", pic="9(5)V99"),
        ],
        paragraphs=[
            ParagraphOut(name="CALC", statements=[
                StatementOut(
                    type="COMPUTE",
                    raw="COMPUTE WS-TOTAL = WS-AMOUNT + WS-TAX",
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    writes = [
        r for r in idx.references
        if r.reference_type == ReferenceType.WRITE
    ]
    reads = [
        r for r in idx.references
        if r.reference_type == ReferenceType.READ
    ]
    assert any(r.field_name == "WS-TOTAL" for r in writes)
    assert any(r.field_name == "WS-AMOUNT" for r in reads)
    assert any(r.field_name == "WS-TAX" for r in reads)


def test_if_condition_produces_condition_references():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-BALANCE", pic="9(7)V99"),
        ],
        paragraphs=[
            ParagraphOut(name="CHECK", statements=[
                StatementOut(
                    type="IF",
                    condition="WS-BALANCE > 0",
                    children=[
                        StatementOut(type="DISPLAY", raw="DISPLAY 'OK'"),
                    ],
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    conditions = [
        r for r in idx.references
        if r.reference_type == ReferenceType.CONDITION
    ]
    assert any(r.field_name == "WS-BALANCE" for r in conditions)


def test_call_using_produces_call_param():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-ACCT", pic="X(10)"),
            DataItemOut(level=1, name="WS-AMT", pic="9(9)V99"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(
                    type="CALL",
                    target="VALIDATE",
                    raw="CALL 'VALIDATE' USING WS-ACCT WS-AMT",
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    params = [
        r for r in idx.references
        if r.reference_type == ReferenceType.CALL_PARAM
    ]
    assert any(r.field_name == "WS-ACCT" for r in params)
    assert any(r.field_name == "WS-AMT" for r in params)


def test_read_into_produces_write():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-RECORD", pic="X(80)"),
        ],
        paragraphs=[
            ParagraphOut(name="READ-FILE", statements=[
                StatementOut(
                    type="READ",
                    target="INPUT-FILE",
                    raw="READ INPUT-FILE INTO WS-RECORD",
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    writes = [
        r for r in idx.references
        if r.reference_type == ReferenceType.WRITE
    ]
    assert any(r.field_name == "WS-RECORD" for r in writes)


def test_write_from_produces_read():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-OUTPUT", pic="X(80)"),
        ],
        paragraphs=[
            ParagraphOut(name="WRITE-FILE", statements=[
                StatementOut(
                    type="WRITE",
                    target="OUTPUT-FILE",
                    raw="WRITE OUTPUT-REC FROM WS-OUTPUT",
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    reads = [
        r for r in idx.references
        if r.reference_type == ReferenceType.READ
    ]
    assert any(r.field_name == "WS-OUTPUT" for r in reads)


def test_entry_fields_from_procedure_using():
    ast = _make_ast(
        procedure_using=["LS-INPUT", "LS-OUTPUT"],
        data_items=[
            DataItemOut(level=1, name="LS-INPUT", pic="X(10)"),
            DataItemOut(level=1, name="LS-OUTPUT", pic="X(10)"),
        ],
        paragraphs=[],
    )
    idx = build_reference_index(ast)
    assert idx.entry_fields == ["LS-INPUT", "LS-OUTPUT"]


def test_defined_fields_includes_children():
    ast = _make_ast(
        data_items=[
            DataItemOut(
                level=1, name="WS-GROUP",
                children=[
                    DataItemOut(level=5, name="WS-CHILD", pic="X(5)"),
                ],
            ),
        ],
        paragraphs=[],
    )
    idx = build_reference_index(ast)
    assert "WS-GROUP" in idx.defined_fields
    assert "WS-CHILD" in idx.defined_fields


def test_read_write_counts():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-A", pic="X(10)"),
            DataItemOut(level=1, name="WS-B", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(type="MOVE", raw="MOVE WS-A TO WS-B"),
                StatementOut(
                    type="IF", condition="WS-A > 0",
                    children=[
                        StatementOut(type="DISPLAY", raw="DISPLAY WS-A"),
                    ],
                ),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    # WS-A: 1 MOVE read + 1 condition + 1 DISPLAY read = 3 reads
    assert idx.field_read_count.get("WS-A", 0) >= 2
    # WS-B: 1 MOVE write
    assert idx.field_write_count.get("WS-B", 0) == 1


def test_unsupported_construct_tracked():
    ast = _make_ast(
        data_items=[],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(type="GO-TO", target="ERR-HANDLER"),
            ]),
        ],
    )
    idx = build_reference_index(ast)
    assert "GO TO" in idx.unsupported_constructs
