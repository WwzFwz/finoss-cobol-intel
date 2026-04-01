"""Unit tests for data flow analysis."""

from cobol_intel.analysis.data_flow import analyze_data_flow
from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.data_flow_output import FlowType


def _make_ast(**kwargs) -> ASTOutput:
    defaults = dict(program_id="TEST", file_path="test.cbl", parser_name="antlr4")
    defaults.update(kwargs)
    return ASTOutput(**defaults)


def test_move_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-SRC", pic="X(10)"),
            DataItemOut(level=1, name="WS-DST", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(type="MOVE", raw="MOVE WS-SRC TO WS-DST"),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    move_edges = [e for e in graph.edges if e.flow_type == FlowType.MOVE]
    assert len(move_edges) == 1
    assert move_edges[0].source_field == "WS-SRC"
    assert move_edges[0].target_field == "WS-DST"


def test_compute_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-TOTAL", pic="9(9)V99"),
            DataItemOut(level=1, name="WS-AMT", pic="9(9)V99"),
            DataItemOut(level=1, name="WS-TAX", pic="9(5)V99"),
        ],
        paragraphs=[
            ParagraphOut(name="CALC", statements=[
                StatementOut(
                    type="COMPUTE",
                    raw="COMPUTE WS-TOTAL = WS-AMT + WS-TAX",
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    compute_edges = [
        e for e in graph.edges if e.flow_type == FlowType.COMPUTE
    ]
    assert len(compute_edges) == 2
    sources = {e.source_field for e in compute_edges}
    assert "WS-AMT" in sources
    assert "WS-TAX" in sources
    assert all(e.target_field == "WS-TOTAL" for e in compute_edges)


def test_read_into_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-RECORD", pic="X(80)"),
        ],
        paragraphs=[
            ParagraphOut(name="READ-IT", statements=[
                StatementOut(
                    type="READ",
                    target="INPUT-FILE",
                    raw="READ INPUT-FILE INTO WS-RECORD",
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    read_edges = [
        e for e in graph.edges if e.flow_type == FlowType.READ_INTO
    ]
    assert len(read_edges) == 1
    assert read_edges[0].source_field == "INPUT-FILE"
    assert read_edges[0].target_field == "WS-RECORD"


def test_write_from_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-OUTPUT", pic="X(80)"),
        ],
        paragraphs=[
            ParagraphOut(name="WRITE-IT", statements=[
                StatementOut(
                    type="WRITE",
                    target="OUTPUT-FILE",
                    raw="WRITE OUTPUT-REC FROM WS-OUTPUT",
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    write_edges = [
        e for e in graph.edges if e.flow_type == FlowType.WRITE_FROM
    ]
    assert len(write_edges) == 1
    assert write_edges[0].source_field == "WS-OUTPUT"
    assert write_edges[0].target_field == "OUTPUT-REC"


def test_call_using_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-ACCT", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(
                    type="CALL",
                    target="VALIDATE",
                    raw="CALL 'VALIDATE' USING WS-ACCT",
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    call_edges = [
        e for e in graph.edges if e.flow_type == FlowType.CALL_PARAM
    ]
    assert len(call_edges) == 1
    assert call_edges[0].source_field == "WS-ACCT"
    assert call_edges[0].target_field == "VALIDATE"


def test_condition_creates_edge():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-BAL", pic="9(7)V99"),
        ],
        paragraphs=[
            ParagraphOut(name="CHECK", statements=[
                StatementOut(
                    type="IF",
                    condition="WS-BAL > 0",
                    children=[
                        StatementOut(type="DISPLAY", raw="DISPLAY 'OK'"),
                    ],
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    cond_edges = [
        e for e in graph.edges
        if e.flow_type == FlowType.CONDITION_READ
    ]
    assert len(cond_edges) == 1
    assert cond_edges[0].source_field == "WS-BAL"
    assert cond_edges[0].target_field == ""


def test_entry_fields_from_procedure_using():
    ast = _make_ast(
        procedure_using=["LS-INPUT", "LS-OUTPUT"],
        data_items=[
            DataItemOut(level=1, name="LS-INPUT", pic="X(10)"),
            DataItemOut(level=1, name="LS-OUTPUT", pic="X(10)"),
        ],
        paragraphs=[],
    )
    graph = analyze_data_flow(ast)
    assert graph.entry_fields == ["LS-INPUT", "LS-OUTPUT"]


def test_output_fields_from_write_and_call():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-DATA", pic="X(80)"),
            DataItemOut(level=1, name="WS-PARAM", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(
                    type="WRITE",
                    target="OUT-FILE",
                    raw="WRITE OUT-REC FROM WS-DATA",
                ),
                StatementOut(
                    type="CALL",
                    target="PROC",
                    raw="CALL 'PROC' USING WS-PARAM",
                ),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    assert "WS-DATA" in graph.output_fields
    assert "WS-PARAM" in graph.output_fields


def test_mermaid_output():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-A", pic="X(10)"),
            DataItemOut(level=1, name="WS-B", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(type="MOVE", raw="MOVE WS-A TO WS-B"),
            ]),
        ],
    )
    graph = analyze_data_flow(ast)
    mermaid = graph.to_mermaid()
    assert "graph LR" in mermaid
    assert "WS-A" in mermaid
    assert "WS-B" in mermaid


def test_empty_program():
    ast = _make_ast(paragraphs=[], data_items=[])
    graph = analyze_data_flow(ast)
    assert graph.edges == []
    assert graph.field_read_count == {}
