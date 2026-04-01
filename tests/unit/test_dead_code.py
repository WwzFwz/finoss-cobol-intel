"""Unit tests for dead code detection."""

from cobol_intel.analysis.cfg_builder import build_cfg
from cobol_intel.analysis.dead_code import detect_dead_code
from cobol_intel.analysis.reference_indexer import build_reference_index
from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.dead_code_output import Confidence, DeadCodeType


def _make_ast(**kwargs) -> ASTOutput:
    defaults = dict(program_id="TEST", file_path="test.cbl", parser_name="antlr4")
    defaults.update(kwargs)
    return ASTOutput(**defaults)


def test_unreachable_paragraph_detected():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="PERFORM", target="PROCESS"),
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="PROCESS", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'PROCESSING'"),
        ]),
        ParagraphOut(name="DEAD-PARA", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'NEVER REACHED'"),
        ]),
    ])
    cfg = build_cfg(ast)
    report = detect_dead_code(ast, cfg=cfg)
    dead_names = [i.name for i in report.items]
    assert "DEAD-PARA" in dead_names
    dead_item = next(
        i for i in report.items if i.name == "DEAD-PARA"
    )
    assert dead_item.type == DeadCodeType.UNREACHABLE_PARAGRAPH


def test_reachable_paragraph_not_flagged():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="PERFORM", target="VALIDATE"),
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="VALIDATE", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'OK'"),
        ]),
    ])
    cfg = build_cfg(ast)
    report = detect_dead_code(ast, cfg=cfg)
    unreachable = [
        i for i in report.items
        if i.type == DeadCodeType.UNREACHABLE_PARAGRAPH
    ]
    assert len(unreachable) == 0


def test_unused_data_item_detected():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-USED", pic="X(10)"),
            DataItemOut(level=1, name="WS-UNUSED", pic="X(10)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(
                    type="MOVE",
                    raw="MOVE 'HELLO' TO WS-USED",
                ),
            ]),
        ],
    )
    ref_idx = build_reference_index(ast)
    report = detect_dead_code(ast, reference_index=ref_idx)
    unused = [
        i for i in report.items
        if i.type == DeadCodeType.UNUSED_DATA_ITEM
    ]
    unused_names = [u.name for u in unused]
    assert "WS-UNUSED" in unused_names
    assert "WS-USED" not in unused_names


def test_trivially_dead_branch_detected():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(
                type="IF",
                condition="WS-X = WS-X",
                children=[
                    StatementOut(type="DISPLAY", raw="DISPLAY 'ALWAYS'"),
                ],
            ),
        ]),
    ])
    report = detect_dead_code(ast)
    dead = [
        i for i in report.items
        if i.type == DeadCodeType.DEAD_BRANCH
    ]
    assert len(dead) == 1
    assert "always true" in dead[0].reason


def test_go_to_adds_warning_and_lowers_confidence():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="GO-TO", target="ERROR-HANDLER"),
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="PROCESS", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'PROC'"),
        ]),
        ParagraphOut(name="ERROR-HANDLER", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'ERROR'"),
        ]),
    ])
    cfg = build_cfg(ast)
    report = detect_dead_code(ast, cfg=cfg)
    assert len(report.warnings) >= 1
    assert any("GO TO" in w for w in report.warnings)
    # Unreachable paragraphs should have MEDIUM confidence when GO TO present
    unreachable = [
        i for i in report.items
        if i.type == DeadCodeType.UNREACHABLE_PARAGRAPH
    ]
    for item in unreachable:
        assert item.confidence == Confidence.MEDIUM


def test_mixed_dead_code_scenario():
    ast = _make_ast(
        data_items=[
            DataItemOut(level=1, name="WS-ACTIVE", pic="X(10)"),
            DataItemOut(level=1, name="WS-ORPHAN", pic="9(5)"),
        ],
        paragraphs=[
            ParagraphOut(name="MAIN", statements=[
                StatementOut(type="PERFORM", target="PROCESS"),
                StatementOut(type="STOP-RUN"),
            ]),
            ParagraphOut(name="PROCESS", statements=[
                StatementOut(
                    type="MOVE", raw="MOVE 'X' TO WS-ACTIVE",
                ),
            ]),
            ParagraphOut(name="ORPHAN-PARA", statements=[
                StatementOut(type="DISPLAY", raw="DISPLAY 'ORPHAN'"),
            ]),
        ],
    )
    cfg = build_cfg(ast)
    ref_idx = build_reference_index(ast)
    report = detect_dead_code(ast, cfg=cfg, reference_index=ref_idx)
    types = {i.type for i in report.items}
    assert DeadCodeType.UNREACHABLE_PARAGRAPH in types
    assert DeadCodeType.UNUSED_DATA_ITEM in types
    assert report.total_dead >= 2


def test_empty_program_no_dead_code():
    ast = _make_ast(paragraphs=[], data_items=[])
    report = detect_dead_code(ast)
    assert report.total_dead == 0
    assert report.items == []


def test_fallback_without_cfg():
    """Dead code detection works without CFG (uses statement scanning)."""
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="PERFORM", target="PROCESS"),
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="PROCESS", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'OK'"),
        ]),
        ParagraphOut(name="UNREACHABLE", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'DEAD'"),
        ]),
    ])
    report = detect_dead_code(ast, cfg=None)
    dead_names = [
        i.name for i in report.items
        if i.type == DeadCodeType.UNREACHABLE_PARAGRAPH
    ]
    assert "UNREACHABLE" in dead_names
