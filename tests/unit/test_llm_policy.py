"""Unit tests for model governance helpers."""

from cobol_intel.contracts.governance import DataSensitivity, DeploymentTier
from cobol_intel.llm.policy import evaluate_model_policy, resolve_preset
from cobol_intel.service.governance import should_redact_prompts


def test_resolve_preset_returns_expected_backend():
    preset = resolve_preset("local-only")
    assert preset.backend == "ollama"
    assert preset.deployment_tier == DeploymentTier.LOCAL_ONLY


def test_high_sensitivity_cloud_backend_gets_warning():
    deployment_tier, warnings = evaluate_model_policy(
        backend_name="openai",
        model_id="gpt-5-mini",
        sensitivity=DataSensitivity.HIGH,
    )
    assert deployment_tier == DeploymentTier.CLOUD
    assert warnings


def test_unapproved_model_is_flagged():
    _, warnings = evaluate_model_policy(
        backend_name="openai",
        model_id="custom-model",
        sensitivity=DataSensitivity.LOW,
    )
    assert any("approved registry" in warning for warning in warnings)


def test_should_redact_for_sensitive_cloud_runs():
    assert should_redact_prompts("openai", DataSensitivity.RESTRICTED) is True
    assert should_redact_prompts("ollama", DataSensitivity.RESTRICTED) is False
