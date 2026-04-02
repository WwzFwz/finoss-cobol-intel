"""Unit tests for composite cache key behavior."""

from __future__ import annotations

from cobol_intel.service.cache import CacheKey, make_cache_key


def _base_key() -> CacheKey:
    return make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )


def test_same_inputs_produce_same_digest():
    assert _base_key().hex_digest() == _base_key().hex_digest()


def test_different_source_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="DIFFERENT SOURCE",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_analysis_payload_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"OTHER"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_parser_version_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v2",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_policy_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json='{"strict": true}',
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_backend_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="claude",
        model="gpt-4o",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_model_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-3.5-turbo",
        mode="technical",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_mode_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="business",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_context_version_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        context_version="explain-context-v2",
        tool_version="0.3.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_different_tool_version_different_digest():
    k1 = _base_key()
    k2 = make_cache_key(
        source_text="IDENTIFICATION DIVISION. PROGRAM-ID. PAYMENT.",
        analysis_payload_json='{"ast":{"program_id":"PAYMENT"}}',
        parser_version="antlr4-v1",
        policy_config_json=None,
        backend="openai",
        model="gpt-4o",
        mode="technical",
        tool_version="0.4.0",
    )
    assert k1.hex_digest() != k2.hex_digest()


def test_cache_key_is_frozen():
    key = _base_key()
    try:
        key.source_hash = "changed"
        assert False, "Should not be mutable"
    except AttributeError:
        pass
