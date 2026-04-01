"""Contract tests for DataFlowGraph schema."""

from cobol_intel.contracts.data_flow_output import (
    DataFlowEdge,
    DataFlowGraph,
    FlowType,
)


def test_data_flow_schema_version():
    graph = DataFlowGraph(program_id="TEST")
    assert graph.schema_version == "1.0"


def test_flow_type_values():
    assert FlowType.MOVE.value == "move"
    assert FlowType.COMPUTE.value == "compute"
    assert FlowType.READ_INTO.value == "read_into"
    assert FlowType.WRITE_FROM.value == "write_from"
    assert FlowType.CALL_PARAM.value == "call_param"
    assert FlowType.CONDITION_READ.value == "condition_read"


def test_data_flow_edge_defaults():
    edge = DataFlowEdge(
        source_field="WS-A",
        flow_type=FlowType.MOVE,
    )
    assert edge.target_field == ""
    assert edge.paragraph == ""


def test_data_flow_roundtrip():
    graph = DataFlowGraph(
        program_id="PAYMENT",
        file_path="payment.cbl",
        edges=[
            DataFlowEdge(
                source_field="WS-AMOUNT",
                target_field="WS-TOTAL",
                flow_type=FlowType.MOVE,
                paragraph="CALC",
                program_id="PAYMENT",
            ),
        ],
        field_read_count={"WS-AMOUNT": 2},
        field_write_count={"WS-TOTAL": 1},
        entry_fields=["LS-INPUT"],
        output_fields=["WS-OUTPUT"],
    )
    data = graph.model_dump()
    restored = DataFlowGraph.model_validate(data)
    assert restored.program_id == "PAYMENT"
    assert len(restored.edges) == 1
    assert restored.edges[0].flow_type == FlowType.MOVE
    assert restored.entry_fields == ["LS-INPUT"]


def test_to_mermaid_output():
    graph = DataFlowGraph(
        program_id="TEST",
        edges=[
            DataFlowEdge(
                source_field="WS-A",
                target_field="WS-B",
                flow_type=FlowType.MOVE,
            ),
        ],
        entry_fields=["LS-IN"],
        output_fields=["WS-OUT"],
    )
    mermaid = graph.to_mermaid()
    assert "graph LR" in mermaid
    assert "WS-A -->|MOVE| WS-B" in mermaid
    assert "LS-IN" in mermaid
    assert "WS-OUT" in mermaid


def test_to_mermaid_empty():
    graph = DataFlowGraph(program_id="EMPTY")
    mermaid = graph.to_mermaid()
    assert "No data flow detected" in mermaid
