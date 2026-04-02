"""Parser PoC corpus tests.

Tests the lark parser against all COBOL samples to evaluate:
- Parse success/failure
- Program ID extraction
- Data item count and hierarchy
- Paragraph count
- Statement type recognition

Results form the basis for parser decision (ADR-006).
"""

from pathlib import Path

import pytest

from cobol_intel.parsers.base import ParseResult
from cobol_intel.parsers.lark_parser import LarkCOBOLParser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"
COPYBOOKS_DIR = Path(__file__).parent.parent.parent / "copybooks"


def parse_sample(rel_path: str, copybook_dirs: list[Path] | None = None) -> ParseResult:
    """Helper: preprocess + parse a sample file."""
    path = SAMPLES_DIR / rel_path
    source = path.read_text(encoding="utf-8")

    dirs = copybook_dirs or []
    pp = COBOLPreprocessor(copybook_dirs=[str(d) for d in dirs])
    preprocessed = pp.preprocess(source, file_path=str(path))

    parser = LarkCOBOLParser()
    return parser.parse(preprocessed.text, file_path=str(path))


# =====================================================================
# Sample 1: hello.cbl — simplest fixed-format program
# =====================================================================
class TestHello:
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
        stmts = self.result.paragraphs[0].statements
        types = [s.type for s in stmts]
        assert "DISPLAY" in types
        assert "STOP-RUN" in types


# =====================================================================
# Sample 2: calc.cbl — IF, EVALUATE, arithmetic
# =====================================================================
class TestCalc:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("fixed_format/calc.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CALC"

    def test_data_items(self):
        names = [d.name for d in self._flat_items()]
        assert "WS-NUM1" in names
        assert "WS-NUM2" in names
        assert "WS-RESULT" in names
        assert "WS-OPERATION" in names

    def test_data_item_pic(self):
        for item in self._flat_items():
            if item.name == "WS-NUM1":
                assert item.pic == "9(3)"
            elif item.name == "WS-OPERATION":
                assert item.pic == "X"

    def test_paragraphs(self):
        names = [p.name for p in self.result.paragraphs]
        assert "MAIN-PROGRAM" in names
        assert "CALCULATE" in names
        assert "VALIDATE-INPUT" in names

    def test_has_evaluate(self):
        calc = self._paragraph("CALCULATE")
        types = [s.type for s in calc.statements]
        assert "EVALUATE" in types

    def test_has_if(self):
        validate = self._paragraph("VALIDATE-INPUT")
        types = [s.type for s in validate.statements]
        assert "IF" in types

    def _flat_items(self):
        """Flatten data item hierarchy."""
        result = []
        stack = list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result

    def _paragraph(self, name: str):
        for p in self.result.paragraphs:
            if p.name == name:
                return p
        raise ValueError(f"Paragraph {name} not found")


# =====================================================================
# Sample 3: simple.cbl — free-format
# =====================================================================
class TestSimple:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("free_format/simple.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "SIMPLE"

    def test_data_items(self):
        names = [d.name for d in self._flat_items()]
        assert "WS-NAME" in names
        assert "WS-GREETING" in names

    def test_has_string_statement(self):
        para = self.result.paragraphs[0]
        types = [s.type for s in para.statements]
        assert "STRING" in types

    def _flat_items(self):
        result = []
        stack = list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result


# =====================================================================
# Sample 4: customer.cbl — COPY statement
# =====================================================================
class TestCustomer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample(
            "with_copybook/customer.cbl",
            copybook_dirs=[COPYBOOKS_DIR],
        )

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CUSTOMER"

    def test_copybook_data_items_resolved(self):
        names = [d.name for d in self._flat_items()]
        # From CUSTMAST copybook
        assert "CUSTOMER-RECORD" in names
        assert "CUST-ID" in names
        assert "CUST-NAME" in names
        assert "CUST-BALANCE" in names
        # From main program
        assert "WS-TOTAL-BALANCE" in names

    def test_condition_entries(self):
        names = [d.name for d in self._flat_items() if d.is_condition]
        assert "CUST-ACTIVE" in names
        assert "CUST-INACTIVE" in names

    def test_paragraphs(self):
        names = [p.name for p in self.result.paragraphs]
        assert "PROCESS-CUSTOMER" in names

    def _flat_items(self):
        result = []
        stack = list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result


# =====================================================================
# Sample 5: interest.cbl — COMP-3, REDEFINES, CALL, OCCURS, EVALUATE TRUE
# =====================================================================
class TestInterest:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.result = parse_sample("complex/interest.cbl")

    def test_parses_successfully(self):
        assert self.result.success, f"Parse failed: {self.result.errors}"

    def test_program_id(self):
        assert self.result.program_id == "CALCINT"

    def test_comp3_usage(self):
        for item in self._flat_items():
            if item.name == "WS-BALANCE":
                assert item.usage == "COMP-3"

    def test_redefines(self):
        for item in self._flat_items():
            if item.name == "WS-DATE-STR":
                assert item.redefines == "WS-DATE-NUM"

    def test_occurs(self):
        for item in self._flat_items():
            if item.name == "WS-MONTH-ENTRY":
                assert item.occurs == 12

    def test_data_hierarchy(self):
        # WS-ACCOUNT-DATA should have children
        for item in self.result.data_items:
            if item.name == "WS-ACCOUNT-DATA":
                child_names = [c.name for c in item.children]
                assert "WS-ACCOUNT-NUMBER" in child_names
                assert "WS-ACCOUNT-TYPE" in child_names
                assert "WS-BALANCE" in child_names

    def test_88_level_hierarchy(self):
        # ACCT-SAVINGS should be child of WS-ACCOUNT-TYPE
        for item in self._flat_items():
            if item.name == "WS-ACCOUNT-TYPE":
                cond_names = [c.name for c in item.children if c.is_condition]
                assert "ACCT-SAVINGS" in cond_names
                assert "ACCT-CHECKING" in cond_names

    def test_paragraphs(self):
        names = [p.name for p in self.result.paragraphs]
        assert "MAIN-PROGRAM" in names
        assert "DETERMINE-RATE" in names
        assert "CALCULATE-INTEREST" in names

    def test_has_call(self):
        main = self._paragraph("MAIN-PROGRAM")
        types = [s.type for s in main.statements]
        assert "CALL" in types

    def test_has_evaluate(self):
        det = self._paragraph("DETERMINE-RATE")
        types = [s.type for s in det.statements]
        assert "EVALUATE" in types

    def test_has_perform_varying(self):
        calc = self._paragraph("CALCULATE-INTEREST")
        types = [s.type for s in calc.statements]
        assert "PERFORM-VARYING" in types

    def _flat_items(self):
        result = []
        stack = list(self.result.data_items)
        while stack:
            item = stack.pop(0)
            result.append(item)
            stack.extend(item.children)
        return result

    def _paragraph(self, name: str):
        for p in self.result.paragraphs:
            if p.name == name:
                return p
        raise ValueError(f"Paragraph {name} not found")
