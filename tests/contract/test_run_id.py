"""Contract tests for run_id format."""

from cobol_intel.contracts.run_id import generate_run_id, is_valid_run_id


def test_generated_run_id_matches_format():
    rid = generate_run_id()
    assert is_valid_run_id(rid)


def test_run_id_starts_with_run_prefix():
    rid = generate_run_id()
    assert rid.startswith("run_")


def test_run_id_has_correct_length():
    # run_YYYYMMDD_HHMMSS_XXXX = 4 + 8 + 1 + 6 + 1 + 4 = 24 chars
    rid = generate_run_id()
    assert len(rid) == 24


def test_two_run_ids_are_different():
    a = generate_run_id()
    b = generate_run_id()
    assert a != b


def test_valid_run_id_accepted():
    assert is_valid_run_id("run_20260331_143052_a7f3")


def test_invalid_run_ids_rejected():
    assert not is_valid_run_id("")
    assert not is_valid_run_id("run_abc")
    assert not is_valid_run_id("some-uuid-v4-string")
    assert not is_valid_run_id("run_20260331_143052")  # missing suffix
