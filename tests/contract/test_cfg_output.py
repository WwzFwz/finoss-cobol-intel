"""Contract tests for ControlFlowGraph schema."""

from cobol_intel.contracts.cfg_output import CFGBlock, CFGEdge, ControlFlowGraph


def test_cfg_schema_version():
    cfg = ControlFlowGraph(program_id="TEST")
    assert cfg.schema_version == "1.0"


def test_cfg_block_defaults():
    block = CFGBlock(block_id="MAIN:B0", paragraph="MAIN")
    assert block.statement_types == []
    assert block.entry_type == "entry"


def test_cfg_edge_defaults():
    edge = CFGEdge(from_block="A:B0", to_block="B:B0")
    assert edge.edge_type == "sequential"
    assert edge.condition is None


def test_cfg_roundtrip_serialization():
    cfg = ControlFlowGraph(
        program_id="PAYMENT",
        file_path="payment.cbl",
        blocks=[
            CFGBlock(
                block_id="MAIN:B0", paragraph="MAIN",
                statement_types=["PERFORM", "IF"],
            ),
        ],
        edges=[
            CFGEdge(
                from_block="MAIN:B0", to_block="VALIDATE:B0",
                edge_type="perform",
            ),
        ],
        entry_block="MAIN:B0",
        exit_blocks=["CLEANUP:B0"],
        perform_targets={"MAIN": ["VALIDATE"]},
        unsupported_constructs=["GO TO"],
    )
    data = cfg.model_dump()
    restored = ControlFlowGraph.model_validate(data)
    assert restored.program_id == "PAYMENT"
    assert len(restored.blocks) == 1
    assert len(restored.edges) == 1
    assert restored.perform_targets == {"MAIN": ["VALIDATE"]}
    assert restored.unsupported_constructs == ["GO TO"]
