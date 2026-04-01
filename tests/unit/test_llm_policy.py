"""Unit tests for model governance helpers."""

import json
import shutil
from pathlib import Path

import pytest

from cobol_intel.contracts.governance import DataSensitivity, DeploymentTier
from cobol_intel.llm.policy import (
    PolicyViolationError,
    effective_max_tokens_per_run,
    enforce_model_policy,
    evaluate_model_policy,
    load_policy_config,
    resolve_preset,
)
from cobol_intel.service.governance import should_redact_prompts

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "tests_runtime_policy"


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def test_resolve_preset_returns_expected_backend():
    preset = resolve_preset("local-only")
    assert preset.backend == "ollama"
    assert preset.deployment_tier == DeploymentTier.LOCAL_ONLY


def test_load_policy_config_from_json_file():
    config_path = RUNTIME_DIR / "llm_policy.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "strict_mode": True,
                "max_tokens_per_run": 777,
                "approved_models": {"openai": ["gpt-5-mini"]},
                "presets": {
                    "fast": {
                        "backend": "openai",
                        "model": "gpt-5-mini",
                        "deployment_tier": "cloud",
                        "description": "custom",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_policy_config(config_path)

    assert config.strict_mode is True
    assert config.max_tokens_per_run == 777
    assert config.approved_models["openai"] == {"gpt-5-mini"}


def test_high_sensitivity_cloud_backend_gets_warning():
    deployment_tier, warnings = evaluate_model_policy(
        backend_name="openai",
        model_id="gpt-5-mini",
        sensitivity=DataSensitivity.HIGH,
    )
    assert deployment_tier == DeploymentTier.CLOUD
    assert warnings


def test_local_backend_is_treated_as_local_only():
    deployment_tier, warnings = evaluate_model_policy(
        backend_name="local",
        model_id="models/cobol-local",
        sensitivity=DataSensitivity.RESTRICTED,
    )
    assert deployment_tier == DeploymentTier.LOCAL_ONLY
    assert warnings == []


def test_unapproved_model_is_flagged():
    _, warnings = evaluate_model_policy(
        backend_name="openai",
        model_id="custom-model",
        sensitivity=DataSensitivity.LOW,
    )
    assert any("approved registry" in warning for warning in warnings)


def test_strict_policy_raises_for_sensitive_cloud_usage():
    with pytest.raises(PolicyViolationError):
        enforce_model_policy(
            backend_name="openai",
            model_id="gpt-5-mini",
            sensitivity=DataSensitivity.RESTRICTED,
            strict_mode=True,
        )


def test_effective_max_tokens_uses_config_default():
    config = load_policy_config()
    assert effective_max_tokens_per_run(config, 123) == 123
    assert effective_max_tokens_per_run(config, None) == config.max_tokens_per_run


def test_should_redact_for_sensitive_cloud_runs():
    assert should_redact_prompts("openai", DataSensitivity.RESTRICTED) is True
    assert should_redact_prompts("ollama", DataSensitivity.RESTRICTED) is False
    assert should_redact_prompts("local", DataSensitivity.RESTRICTED) is False
