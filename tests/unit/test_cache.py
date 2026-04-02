"""Unit tests for the explanation cache."""

import shutil
from pathlib import Path

from cobol_intel.contracts.explanation_output import ExplanationMode, ExplanationOutput
from cobol_intel.service.cache import CacheKey, ExplanationCache, make_cache_key

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "tests_runtime_cache"


def _sample_explanation() -> ExplanationOutput:
    return ExplanationOutput(
        program_id="PAYMENT",
        file_path="payment.cbl",
        mode=ExplanationMode.TECHNICAL,
        backend="openai",
        model="gpt-4o",
        program_summary="Processes payments.",
        tokens_used=500,
    )


def _sample_key() -> CacheKey:
    return make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast": {"program_id": "PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def _fresh_cache_dir(name: str) -> Path:
    cache_dir = RUNTIME_DIR / name
    shutil.rmtree(cache_dir, ignore_errors=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def test_cache_miss():
    cache = ExplanationCache(cache_dir=_fresh_cache_dir("miss"))
    result = cache.get(_sample_key())
    assert result is None


def test_cache_put_and_get():
    cache = ExplanationCache(cache_dir=_fresh_cache_dir("put_get"))
    key = _sample_key()
    explanation = _sample_explanation()
    cache.put(key, explanation)
    cached = cache.get(key)
    assert cached is not None
    assert cached.program_id == "PAYMENT"
    assert cached.tokens_used == 500


def test_cache_invalidate():
    cache = ExplanationCache(cache_dir=_fresh_cache_dir("invalidate"))
    key = _sample_key()
    cache.put(key, _sample_explanation())
    assert cache.invalidate(key) is True
    assert cache.get(key) is None
    assert cache.invalidate(key) is False


def test_cache_clear():
    cache = ExplanationCache(cache_dir=_fresh_cache_dir("clear"))
    for i in range(3):
        key = make_cache_key(
            source_text=f"source{i}",
            analysis_payload_json=f'{{"index": {i}}}',
            parser_version="antlr4",
            policy_config_json=None,
            backend="openai",
            model="gpt-4o",
            mode="technical",
            tool_version="0.3.0",
        )
        cache.put(key, _sample_explanation())
    removed = cache.clear()
    assert removed == 3
    assert cache.get(_sample_key()) is None


def test_cache_clear_empty_dir():
    cache = ExplanationCache(cache_dir=RUNTIME_DIR / "nonexistent")
    assert cache.clear() == 0


def test_cache_corrupted_file():
    cache_dir = _fresh_cache_dir("corrupted")
    cache = ExplanationCache(cache_dir=cache_dir)
    key = _sample_key()
    (cache_dir / f"{key.hex_digest()}.json").write_text("not json", encoding="utf-8")
    assert cache.get(key) is None
