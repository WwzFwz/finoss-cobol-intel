"""Evaluation tests: benchmark parse success and token savings."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from benchmark import run_benchmark

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
COPYBOOKS_DIR = Path(__file__).resolve().parents[2] / "copybooks"


def test_benchmark_parse_success_rate_above_90_pct():
    copybook_dirs = [COPYBOOKS_DIR] if COPYBOOKS_DIR.exists() else []
    results = run_benchmark(SAMPLES_DIR, copybook_dirs)

    assert len(results) > 0
    success = sum(1 for r in results if r.parse_success)
    rate = success / len(results)
    assert rate >= 0.90, f"Parse success rate {rate:.0%} below 90%"


def test_benchmark_token_savings_positive():
    copybook_dirs = [COPYBOOKS_DIR] if COPYBOOKS_DIR.exists() else []
    results = run_benchmark(SAMPLES_DIR, copybook_dirs)

    parsed = [r for r in results if r.parse_success]
    assert len(parsed) > 0

    for r in parsed:
        assert r.prompt_chars > 0, f"No prompt generated for {r.file_path}"
