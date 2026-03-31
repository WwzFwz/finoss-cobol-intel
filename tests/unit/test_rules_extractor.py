"""Unit tests for business rules extraction."""

from pathlib import Path

from cobol_intel.analysis.rules_extractor import extract_rules
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
COPYBOOKS_DIR = REPO_ROOT / "copybooks"


def _parse(rel_path: str, *, with_copybooks: bool = False):
    path = SAMPLES_DIR / rel_path
    copybook_dirs = [str(COPYBOOKS_DIR)] if with_copybooks else []
    preprocessor = COBOLPreprocessor(copybook_dirs=copybook_dirs)
    preprocessed = preprocessor.preprocess(path.read_text(encoding="utf-8"), file_path=str(path))
    return ANTLR4Parser().parse(preprocessed.text, file_path=str(path))


def test_extract_rules_finds_if_and_evaluate_rules():
    result = _parse("complex/payment.cbl")
    rules = extract_rules(result, file_path=result.file_path)

    rule_types = [rule.type for rule in rules.rules]
    conditions = [rule.condition for rule in rules.rules]
    assert "IF" in rule_types
    assert "EVALUATE" in rule_types
    assert "STATUS-OK" in conditions
    assert "EVALUATE TRUE" in conditions


def test_extract_rules_includes_condition_88_entries():
    result = _parse("with_copybook/customer.cbl", with_copybooks=True)
    rules = extract_rules(result, file_path=result.file_path)

    conditions = [rule.condition for rule in rules.rules if rule.type == "CONDITION-88"]
    assert "CUST-ACTIVE = A" in conditions
    assert "CUST-INACTIVE = I" in conditions


def test_extract_rules_keeps_paragraph_context():
    result = _parse("complex/acctval.cbl")
    rules = extract_rules(result, file_path=result.file_path)

    matching = [rule for rule in rules.rules if rule.condition == "WS-ACCT-NUM=SPACES"]
    assert matching
    assert matching[0].paragraph == "VALIDATE-ACCOUNT"
