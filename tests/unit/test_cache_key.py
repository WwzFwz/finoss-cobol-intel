"""Unit tests for composite cache key behavior."""

from cobol_intel.service.cache import CacheKey, make_cache_key


def _base_key() -> CacheKey:
    return make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
    )


def test_same_inputs_produce_same_digest():
    k1 = _base_key()
    k2 = _base_key()
    assert k1.hex_digest() == k2.hex_digest()


def test_different_source_different_digest():
    k1 = _base_key()
    k2 = make_cache_key("DIFFERENT SOURCE", "antlr4-v1", None, "openai", "gpt-4o", "technical")
    assert k1.hex_digest() != k2.hex_digest()


def test_different_parser_version_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v2", None, "openai", "gpt-4o", "technical",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_policy_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v1", '{"strict": true}', "openai", "gpt-4o", "technical",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_backend_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v1", None, "claude", "gpt-4o", "technical",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_model_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v1", None, "openai", "gpt-3.5-turbo", "technical",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_mode_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v1", None, "openai", "gpt-4o", "business",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_context_version_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        "IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        "antlr4-v1",
        None,
        "openai",
        "gpt-4o",
        "technical",
        context_version="explain-context-v2",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_cache_key_is_frozen():
    key = _base_key()
    try:
        key.source_hash = "changed"
        assert False, "Should not be mutable"
    except AttributeError:
        pass
