"""Regression baselines for Phase 1 parser and artifact outputs."""

from __future__ import annotations

import json
from pathlib import Path

from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.analysis.rules_extractor import extract_rules
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor
from cobol_intel.service.pipeline import to_ast_output

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
COPYBOOKS_DIR = REPO_ROOT / "copybooks"
EXPECTED_DIR = REPO_ROOT / "tests" / "fixtures" / "expected"


def _parse(rel_path: str):
    parser = ANTLR4Parser()
    source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    preprocessed = COBOLPreprocessor(copybook_dirs=[COPYBOOKS_DIR]).preprocess(
        source,
        file_path=rel_path,
    )
    return parser.parse(preprocessed.text, file_path=rel_path)


def _load_expected(name: str):
    path = EXPECTED_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_fileio_ast_matches_baseline():
    result = _parse("samples/complex/fileio.cbl")
    actual = to_ast_output(result, file_path="samples/complex/fileio.cbl").model_dump(
        mode="json"
    )

    assert actual == _load_expected("fileio_ast.json")


def test_payment_rules_match_baseline():
    result = _parse("samples/complex/payment.cbl")
    actual = extract_rules(result, file_path="samples/complex/payment.cbl").model_dump(
        mode="json"
    )

    assert actual == _load_expected("payment_rules.json")


def test_complex_call_graph_matches_baseline():
    results = [
        _parse("samples/complex/acctval.cbl"),
        _parse("samples/complex/interest.cbl"),
        _parse("samples/complex/payment.cbl"),
    ]
    actual = build_call_graph(results).model_dump(mode="json")

    assert actual == _load_expected("complex_call_graph.json")
