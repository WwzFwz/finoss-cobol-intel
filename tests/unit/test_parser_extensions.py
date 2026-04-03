"""Unit tests for parser coverage beyond the Phase 1 MVP subset."""

from pathlib import Path

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


def _flatten(items):
    result = []
    stack = list(items)
    while stack:
        item = stack.pop(0)
        result.append(item)
        stack.extend(item.children)
    return result


def test_procedure_division_using_exec_sql_and_string_ops_parse():
    result = _parse("complex/sqlops.cbl")

    assert result.success, result.errors
    assert result.procedure_using == ["LK-REQUEST"]

    main = next(paragraph for paragraph in result.paragraphs if paragraph.name == "MAIN-PROGRAM")
    types = [statement.type for statement in main.statements]
    assert "UNSTRING" in types
    assert "INSPECT" in types
    assert "EXEC-SQL" in types


def test_file_io_statements_parse():
    result = _parse("complex/filebatch.cbl")

    assert result.success, result.errors
    main = next(paragraph for paragraph in result.paragraphs if paragraph.name == "MAIN-PROGRAM")
    types = [statement.type for statement in main.statements]
    assert "OPEN" in types
    assert "READ" in types
    assert "WRITE" in types
    assert "REWRITE" in types
    assert "CLOSE" in types

    read_stmt = next(statement for statement in main.statements if statement.type == "READ")
    assert [child.type for child in read_stmt.children] == ["MOVE"]


def test_copy_replacing_sample_resolves_into_data_items():
    result = _parse("with_copybook/replacing_customer.cbl", with_copybooks=True)

    assert result.success, result.errors
    names = [item.name for item in _flatten(result.data_items)]
    assert "WS-CUST-RECORD" in names
    assert "WS-CUST-ID" in names
    assert "WS-CUST-NAME" in names


def test_perform_thru_and_exec_cics_parse():
    result = _parse("complex/cicsflow.cbl")

    assert result.success, result.errors
    main = next(paragraph for paragraph in result.paragraphs if paragraph.name == "MAIN-PROGRAM")
    types = [statement.type for statement in main.statements]
    assert "PERFORM-THRU" in types
    assert "EXEC-CICS" in types

    perform_stmt = next(
        statement
        for statement in main.statements
        if statement.type == "PERFORM-THRU"
    )
    assert perform_stmt.target == "INIT-ROUTINE THRU FINISH-ROUTINE"

    exec_cics_stmt = next(
        statement
        for statement in main.statements
        if statement.type == "EXEC-CICS"
    )
    assert exec_cics_stmt.raw.startswith("EXECCICS")
