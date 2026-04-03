"""Phase 1 parser corpus smoke tests.

Ensures both parser implementations can handle the current 10-sample corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.lark_parser import LarkCOBOLParser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
COPYBOOKS_DIR = REPO_ROOT / "copybooks"

CORPUS_SAMPLES = [
    "complex/acctval.cbl",
    "complex/cicsflow.cbl",
    "complex/filebatch.cbl",
    "complex/fileio.cbl",
    "complex/interest.cbl",
    "complex/linkdemo.cbl",
    "complex/payment.cbl",
    "complex/sqlops.cbl",
    "fixed_format/calc.cbl",
    "fixed_format/hello.cbl",
    "fixed_format/recon.cbl",
    "free_format/simple.cbl",
    "with_copybook/customer.cbl",
    "with_copybook/replacing_customer.cbl",
]


def _parse_sample(parser, rel_path: str):
    path = SAMPLES_DIR / rel_path
    source = path.read_text(encoding="utf-8")
    copybook_dirs = [COPYBOOKS_DIR] if "with_copybook" in rel_path else []
    preprocessed = COBOLPreprocessor(copybook_dirs=copybook_dirs).preprocess(
        source,
        file_path=rel_path,
    )
    return parser.parse(preprocessed.text, file_path=rel_path)


@pytest.mark.parametrize(
    ("parser_factory", "parser_name"),
    [
        (ANTLR4Parser, "antlr4"),
        (LarkCOBOLParser, "lark-earley"),
    ],
)
@pytest.mark.parametrize("rel_path", CORPUS_SAMPLES)
def test_phase1_corpus_parses_without_crash(parser_factory, parser_name: str, rel_path: str):
    parser = parser_factory()
    result = _parse_sample(parser, rel_path)

    assert result.success, f"{parser_name} failed on {rel_path}: {result.errors}"
    assert result.parser_name == parser_name
