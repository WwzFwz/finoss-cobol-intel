"""ANTLR4 Parser PoC corpus tests.

Same tests as test_parser_poc.py but using the ANTLR4 parser.
Results compared against lark for ADR-006 decision.
"""

from pathlib import Path

import pytest

from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"
COPYBOOKS_DIR = Path(__file__).parent.parent.parent / "copybooks"


def parse_sample(rel_path: str, copybook_dirs: list[Path] | None = None):
    path = SAMPLES_DIR / rel_path
    source = path.read_text(encoding="utf-8")
    dirs = copybook_dirs or []
    pp = COBOLPreprocessor(copybook_dirs=[str(d) for d in dirs])
    preprocessed = pp.preprocess(source, file_path=str(path))
    parser = ANTLR4Parser()
    return parser.parse(preprocessed.text, file_path=str(path))


class TestHelloAntlr:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("fixed_format/hello.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "HELLO"

    def test_no_data_items(self):
        assert len(self.result.data_items) == 0

    def test_has_one_paragraph(self):
        assert len(self.result.paragraphs) == 1
        assert self.result.paragraphs[0].name == "MAIN-PROGRAM"

    def test_has_display_and_stop(self):
        types = [s.type for s in self.result.paragraphs[0].statements]
        assert "DISPLAY" in types
        assert "STOP-RUN" in types


class TestCalcAntlr:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("fixed_format/calc.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CALC"

    def test_data_items(self):
        names = [d.name for d in self._flat()]
        assert "WS-NUM1" in names
        assert "WS-RESULT" in names

    def test_has_evaluate(self):
        calc = next(p for p in self.result.paragraphs if p.name == "CALCULATE")
        assert "EVALUATE" in [s.type for s in calc.statements]

    def test_has_if(self):
        v = next(p for p in self.result.paragraphs if p.name == "VALIDATE-INPUT")
        assert "IF" in [s.type for s in v.statements]

    def _flat(self):
        result, stack = [], list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result


class TestSimpleAntlr:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("free_format/simple.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "SIMPLE"

    def test_has_string_statement(self):
        types = [s.type for s in self.result.paragraphs[0].statements]
        assert "STRING" in types


class TestCustomerAntlr:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample(
            "with_copybook/customer.cbl", copybook_dirs=[COPYBOOKS_DIR]
        )

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CUSTOMER"

    def test_copybook_data_resolved(self):
        names = [d.name for d in self._flat()]
        assert "CUSTOMER-RECORD" in names
        assert "CUST-ID" in names

    def test_condition_entries(self):
        names = [d.name for d in self._flat() if d.is_condition]
        assert "CUST-ACTIVE" in names

    def _flat(self):
        result, stack = [], list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result


class TestInterestAntlr:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("complex/interest.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CALCINT"

    def test_comp3_usage(self):
        for item in self._flat():
            if item.name == "WS-BALANCE":
                assert item.usage == "COMP-3"

    def test_redefines(self):
        for item in self._flat():
            if item.name == "WS-DATE-STR":
                assert item.redefines == "WS-DATE-NUM"

    def test_occurs(self):
        for item in self._flat():
            if item.name == "WS-MONTH-ENTRY":
                assert item.occurs == 12

    def test_data_hierarchy(self):
        for item in self.result.data_items:
            if item.name == "WS-ACCOUNT-DATA":
                child_names = [c.name for c in item.children]
                assert "WS-ACCOUNT-NUMBER" in child_names
                assert "WS-BALANCE" in child_names

    def test_88_level_hierarchy(self):
        for item in self._flat():
            if item.name == "WS-ACCOUNT-TYPE":
                conds = [c.name for c in item.children if c.is_condition]
                assert "ACCT-SAVINGS" in conds

    def test_has_call(self):
        main = next(p for p in self.result.paragraphs if p.name == "MAIN-PROGRAM")
        assert "CALL" in [s.type for s in main.statements]

    def test_has_evaluate(self):
        det = next(p for p in self.result.paragraphs if p.name == "DETERMINE-RATE")
        assert "EVALUATE" in [s.type for s in det.statements]

    def test_has_perform_varying(self):
        calc = next(p for p in self.result.paragraphs if p.name == "CALCULATE-INTEREST")
        assert "PERFORM-VARYING" in [s.type for s in calc.statements]

    def _flat(self):
        result, stack = [], list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result
