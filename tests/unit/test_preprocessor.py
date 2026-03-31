"""Tests for COBOL preprocessor."""

from pathlib import Path

from cobol_intel.parsers.preprocessor import COBOLPreprocessor


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_detect_fixed_format():
    source = "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n"
    pp = COBOLPreprocessor()
    result = pp.preprocess(source)
    assert result.source_format == "fixed"


def test_detect_free_format():
    source = "IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\n"
    pp = COBOLPreprocessor()
    result = pp.preprocess(source)
    assert result.source_format == "free"


def test_fixed_format_strips_sequence_area():
    source = "000100 IDENTIFICATION DIVISION.\n000200 PROGRAM-ID. HELLO.\n"
    pp = COBOLPreprocessor()
    result = pp.preprocess(source)
    assert "000100" not in result.text
    assert "IDENTIFICATION DIVISION." in result.text


def test_fixed_format_removes_comments():
    source = (
        "       IDENTIFICATION DIVISION.\n"
        "      * THIS IS A COMMENT\n"
        "       PROGRAM-ID. HELLO.\n"
    )
    pp = COBOLPreprocessor()
    result = pp.preprocess(source)
    assert "COMMENT" not in result.text
    assert "IDENTIFICATION" in result.text
    assert "PROGRAM-ID" in result.text


def test_uppercase_preserves_strings():
    source = 'DISPLAY "hello world".\n'
    pp = COBOLPreprocessor(source_format="free")
    result = pp.preprocess(source)
    assert '"hello world"' in result.text
    assert "DISPLAY" in result.text


def test_pic_normalization():
    source = "01 WS-NUM PIC 9(5) VALUE 0.\n"
    pp = COBOLPreprocessor(source_format="free")
    result = pp.preprocess(source)
    assert 'PIC "9(5)"' in result.text


def test_pic_normalization_complex():
    source = "05 WS-BAL PIC S9(7)V99 COMP-3.\n"
    pp = COBOLPreprocessor(source_format="free")
    result = pp.preprocess(source)
    assert 'PIC "S9(7)V99"' in result.text
    assert "COMP-3" in result.text


def test_copybook_resolution():
    copybook_dir = REPO_ROOT / "copybooks"
    source = "       COPY CUSTMAST.\n       01 OTHER PIC 9.\n"
    pp = COBOLPreprocessor(copybook_dirs=[str(copybook_dir)])
    result = pp.preprocess(source)

    assert "CUSTOMER-RECORD" in result.text
    assert "CUSTMAST" in result.copybooks_resolved


def test_copybook_missing_warning():
    source = "       COPY NOTEXIST.\n"
    pp = COBOLPreprocessor(copybook_dirs=[])
    result = pp.preprocess(source)
    assert len(result.warnings) > 0
    assert "NOTEXIST" in result.warnings[0]


def test_copybook_circular_dependency_warning():
    copybook_dir = REPO_ROOT / "copybooks"
    source = "       COPY CYCLEA.\n"
    pp = COBOLPreprocessor(copybook_dirs=[str(copybook_dir)])
    result = pp.preprocess(source)

    assert "CYCLE-A-RECORD" in result.text
    assert "CYCLE-B-RECORD" in result.text
    assert any("Circular COPY dependency detected" in warning for warning in result.warnings)


def test_blank_lines_removed():
    source = "IDENTIFICATION DIVISION.\n\n\nPROGRAM-ID. HELLO.\n"
    pp = COBOLPreprocessor(source_format="free")
    result = pp.preprocess(source)
    assert "\n\n" not in result.text
