"""Unit tests for the CFG builder."""

from cobol_intel.analysis.cfg_builder import build_cfg
from cobol_intel.contracts.ast_output import ASTOutput, ParagraphOut, StatementOut


def _make_ast(**kwargs) -> ASTOutput:
    defaults = dict(program_id="TEST", file_path="test.cbl", parser_name="antlr4")
    defaults.update(kwargs)
    return ASTOutput(**defaults)


def test_linear_paragraph_single_block():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'HELLO'"),
            StatementOut(type="STOP-RUN"),
        ]),
    ])
    cfg = build_cfg(ast)
    assert cfg.program_id == "TEST"
    assert len(cfg.blocks) == 1
    assert cfg.blocks[0].block_id == "MAIN:B0"
    assert "DISPLAY" in cfg.blocks[0].statement_types
    assert "STOP-RUN" in cfg.blocks[0].statement_types
    assert cfg.entry_block == "MAIN:B0"


def test_if_creates_branch_blocks():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(
                type="IF",
                condition="WS-X > 0",
                children=[
                    StatementOut(type="DISPLAY", raw="DISPLAY 'POSITIVE'"),
                ],
            ),
        ]),
    ])
    cfg = build_cfg(ast)
    # Should have: the IF block + branch_true block
    assert len(cfg.blocks) >= 2
    branch_blocks = [b for b in cfg.blocks if b.entry_type == "branch_true"]
    assert len(branch_blocks) == 1
    assert "DISPLAY" in branch_blocks[0].statement_types

    # Should have branch edge with condition
    branch_edges = [
        e for e in cfg.edges if e.edge_type == "branch_true"
    ]
    assert len(branch_edges) == 1
    assert branch_edges[0].condition == "WS-X > 0"


def test_if_else_creates_two_branch_blocks():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(
                type="IF",
                condition="WS-FLAG = 'Y'",
                children=[
                    StatementOut(type="DISPLAY", raw="DISPLAY 'YES'"),
                    StatementOut(type="DISPLAY", raw="DISPLAY 'NO'"),
                ],
            ),
        ]),
    ])
    cfg = build_cfg(ast)
    true_blocks = [b for b in cfg.blocks if b.entry_type == "branch_true"]
    false_blocks = [b for b in cfg.blocks if b.entry_type == "branch_false"]
    assert len(true_blocks) == 1
    assert len(false_blocks) == 1


def test_perform_target_recorded():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="PERFORM", target="VALIDATE"),
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="VALIDATE", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'VALIDATING'"),
        ]),
    ])
    cfg = build_cfg(ast)
    assert "MAIN" in cfg.perform_targets
    assert "VALIDATE" in cfg.perform_targets["MAIN"]

    # Should have a perform edge
    perform_edges = [e for e in cfg.edges if e.edge_type == "perform"]
    assert len(perform_edges) >= 1


def test_stop_run_is_exit_block():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'BYE'"),
            StatementOut(type="STOP-RUN"),
        ]),
    ])
    cfg = build_cfg(ast)
    assert len(cfg.exit_blocks) >= 1


def test_goback_is_exit_block():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="GOBACK"),
        ]),
    ])
    cfg = build_cfg(ast)
    assert len(cfg.exit_blocks) >= 1


def test_unsupported_construct_warning():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="GO-TO", target="ERROR-HANDLER"),
        ]),
    ])
    cfg = build_cfg(ast)
    assert "GO TO" in cfg.unsupported_constructs


def test_fallthrough_edge_between_paragraphs():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="INIT", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'INIT'"),
        ]),
        ParagraphOut(name="PROCESS", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'PROCESS'"),
        ]),
    ])
    cfg = build_cfg(ast)
    fallthrough = [e for e in cfg.edges if e.edge_type == "fallthrough"]
    assert len(fallthrough) == 1
    assert fallthrough[0].from_block.startswith("INIT:")
    assert fallthrough[0].to_block.startswith("PROCESS:")


def test_no_fallthrough_after_exit():
    ast = _make_ast(paragraphs=[
        ParagraphOut(name="MAIN", statements=[
            StatementOut(type="STOP-RUN"),
        ]),
        ParagraphOut(name="DEAD", statements=[
            StatementOut(type="DISPLAY", raw="DISPLAY 'UNREACHABLE'"),
        ]),
    ])
    cfg = build_cfg(ast)
    fallthrough = [e for e in cfg.edges if e.edge_type == "fallthrough"]
    assert len(fallthrough) == 0


def test_empty_ast_produces_empty_cfg():
    ast = _make_ast(paragraphs=[])
    cfg = build_cfg(ast)
    assert cfg.blocks == []
    assert cfg.entry_block is None
