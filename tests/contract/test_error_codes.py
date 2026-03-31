"""Contract tests for structured error codes."""

from cobol_intel.contracts.manifest import ErrorCode, RunError


def test_all_error_codes_have_unique_values():
    values = [code.value for code in ErrorCode]
    assert len(values) == len(set(values))


def test_error_code_prefix_categories():
    for code in ErrorCode:
        prefix = code.value[0:2]
        assert prefix[0] == "E"
        assert prefix[1].isdigit()


def test_run_error_serializes_error_code():
    error = RunError(file="test.cbl", code=ErrorCode.LLM_TIMEOUT, module="llm", message="timed out")
    data = error.model_dump(mode="json")
    assert data["code"] == "E3002"
    assert data["module"] == "llm"


def test_run_error_default_code_is_parse_syntax():
    error = RunError(file="test.cbl", message="some error")
    assert error.code == ErrorCode.PARSE_SYNTAX
