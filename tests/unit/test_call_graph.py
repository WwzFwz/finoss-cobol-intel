"""Unit tests for call graph builder."""

from pathlib import Path

from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def _parse(rel_path: str):
    path = SAMPLES_DIR / rel_path
    preprocessor = COBOLPreprocessor()
    preprocessed = preprocessor.preprocess(path.read_text(encoding="utf-8"), file_path=str(path))
    return ANTLR4Parser().parse(preprocessed.text, file_path=str(path))


def test_build_call_graph_collects_static_calls():
    graph = build_call_graph([
        _parse("complex/payment.cbl"),
        _parse("complex/acctval.cbl"),
        _parse("complex/interest.cbl"),
    ])

    edges = {(edge.caller, edge.callee) for edge in graph.edges}
    assert ("PAYMENT", "DATEUTIL") in edges
    assert ("PAYMENT", "BALCHK") in edges
    assert ("CALCINT", "LOGTRX") in edges


def test_build_call_graph_tracks_adjacency_and_entry_points():
    graph = build_call_graph([
        _parse("complex/payment.cbl"),
        _parse("complex/acctval.cbl"),
        _parse("complex/interest.cbl"),
    ])

    assert graph.adjacency["PAYMENT"] == ["BALCHK", "DATEUTIL"]
    assert "ACCTVAL" in graph.entry_points
    assert "LOGTRX" in graph.external_calls
