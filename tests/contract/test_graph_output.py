"""Contract tests for call graph output schema."""

from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput


def test_call_graph_schema_version():
    graph = CallGraphOutput()
    assert graph.schema_version == "1.0"


def test_call_graph_serializes_required_fields():
    graph = CallGraphOutput(
        nodes=["A", "B"],
        edges=[CallEdge(caller="A", callee="B")],
        adjacency={"A": ["B"]},
    )
    data = graph.model_dump()
    required = {"schema_version", "nodes", "edges", "adjacency", "entry_points", "external_calls"}
    assert required.issubset(data.keys())


def test_call_graph_mermaid_rendering():
    graph = CallGraphOutput(
        nodes=["PAYMENT", "DATEUTIL"],
        edges=[CallEdge(caller="PAYMENT", callee="DATEUTIL")],
        adjacency={"PAYMENT": ["DATEUTIL"]},
        external_calls=["DATEUTIL"],
    )
    rendered = graph.to_mermaid()
    assert "graph TD" in rendered
    assert "PAYMENT --> DATEUTIL" in rendered
