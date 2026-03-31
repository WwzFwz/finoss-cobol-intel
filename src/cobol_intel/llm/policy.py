"""Model governance helpers for safe backend selection."""

from __future__ import annotations

from dataclasses import dataclass

from cobol_intel.contracts.governance import DataSensitivity, DeploymentTier


@dataclass(frozen=True)
class ModelPreset:
    name: str
    backend: str
    model: str
    deployment_tier: DeploymentTier
    description: str


APPROVED_MODELS: dict[str, set[str]] = {
    "claude": {"claude-sonnet-4-20250514"},
    "openai": {"gpt-5-mini"},
    "ollama": {"llama3.1:8b"},
}

MODEL_PRESETS: dict[str, ModelPreset] = {
    "fast": ModelPreset(
        name="fast",
        backend="openai",
        model="gpt-5-mini",
        deployment_tier=DeploymentTier.CLOUD,
        description="Fast cloud preset for non-sensitive workloads.",
    ),
    "balanced": ModelPreset(
        name="balanced",
        backend="claude",
        model="claude-sonnet-4-20250514",
        deployment_tier=DeploymentTier.CLOUD,
        description="Balanced cloud preset for high-quality explanations.",
    ),
    "audit": ModelPreset(
        name="audit",
        backend="claude",
        model="claude-sonnet-4-20250514",
        deployment_tier=DeploymentTier.HYBRID,
        description="Higher-scrutiny preset for audit and compliance review.",
    ),
    "local-only": ModelPreset(
        name="local-only",
        backend="ollama",
        model="llama3.1:8b",
        deployment_tier=DeploymentTier.LOCAL_ONLY,
        description="On-prem preset for sensitive or regulated workloads.",
    ),
}


def resolve_preset(name: str) -> ModelPreset:
    """Resolve a named preset or raise a KeyError."""
    return MODEL_PRESETS[name]


def deployment_tier_for_backend(backend_name: str) -> DeploymentTier:
    """Map backend implementations to deployment tiers."""
    if backend_name == "ollama":
        return DeploymentTier.LOCAL_ONLY
    if backend_name in {"claude", "openai"}:
        return DeploymentTier.CLOUD
    return DeploymentTier.HYBRID


def evaluate_model_policy(
    backend_name: str,
    model_id: str,
    sensitivity: DataSensitivity,
) -> tuple[DeploymentTier, list[str]]:
    """Return deployment tier and policy warnings for a model selection."""
    warnings: list[str] = []
    deployment_tier = deployment_tier_for_backend(backend_name)

    approved = _approved_models_get(backend_name)
    if approved and model_id not in approved:
        warnings.append(
            f"Model '{model_id}' is not in the approved registry for backend '{backend_name}'."
        )

    if deployment_tier == DeploymentTier.CLOUD and sensitivity in {
        DataSensitivity.HIGH,
        DataSensitivity.RESTRICTED,
    }:
        warnings.append(
            "Sensitive artifacts are using a cloud backend; prefer the 'local-only' preset or an on-prem model."
        )

    return deployment_tier, warnings


def _approved_models_get(backend_name: str) -> set[str]:
    """Small helper to keep the policy logic readable."""
    return APPROVED_MODELS.get(backend_name, set())
