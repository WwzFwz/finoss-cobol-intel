"""Model governance helpers for safe backend selection."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from cobol_intel.contracts.governance import DataSensitivity, DeploymentTier

_DEFAULT_POLICY_PATH = Path("config") / "llm_policy.json"


@dataclass(frozen=True)
class ModelPreset:
    name: str
    backend: str
    model: str
    deployment_tier: DeploymentTier
    description: str


@dataclass(frozen=True)
class PolicyConfig:
    strict_mode: bool
    max_tokens_per_run: int | None
    approved_models: dict[str, set[str]]
    presets: dict[str, ModelPreset]


class PolicyViolationError(RuntimeError):
    """Raised when a strict governance rule blocks an LLM request."""


_DEFAULT_APPROVED_MODELS: dict[str, set[str]] = {
    "claude": {"claude-sonnet-4-20250514"},
    "openai": {"gpt-5-mini"},
    "ollama": {"llama3.1:8b"},
}

_DEFAULT_PRESETS: dict[str, ModelPreset] = {
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


def load_policy_config(path: str | Path | None = None) -> PolicyConfig:
    """Load policy configuration from JSON or fall back to defaults."""
    resolved_path = _resolve_policy_path(path)
    return _load_policy_config_cached(str(resolved_path) if resolved_path else "")


def resolve_preset(name: str, config: PolicyConfig | None = None) -> ModelPreset:
    """Resolve a named preset or raise KeyError."""
    policy = config or load_policy_config()
    return policy.presets[name]


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
    config: PolicyConfig | None = None,
) -> tuple[DeploymentTier, list[str]]:
    """Return deployment tier and policy warnings for a model selection."""
    policy = config or load_policy_config()
    warnings: list[str] = []
    deployment_tier = deployment_tier_for_backend(backend_name)

    approved = policy.approved_models.get(backend_name, set())
    if approved and model_id and model_id not in approved:
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


def effective_strict_mode(
    config: PolicyConfig | None = None,
    strict_mode: bool | None = None,
) -> bool:
    """Resolve strict mode from caller override, env, or policy config."""
    if strict_mode is not None:
        return strict_mode
    env_value = os.environ.get("COBOL_INTEL_STRICT_POLICY")
    if env_value is not None:
        return env_value.strip().lower() in {"1", "true", "yes", "on"}
    policy = config or load_policy_config()
    return policy.strict_mode


def effective_max_tokens_per_run(
    config: PolicyConfig | None = None,
    max_tokens_per_run: int | None = None,
) -> int | None:
    """Resolve run-level token budget from caller override, env, or policy config."""
    if max_tokens_per_run is not None:
        return max_tokens_per_run
    env_value = os.environ.get("COBOL_INTEL_MAX_TOKENS_PER_RUN")
    if env_value:
        return int(env_value)
    policy = config or load_policy_config()
    return policy.max_tokens_per_run


def enforce_model_policy(
    backend_name: str,
    model_id: str,
    sensitivity: DataSensitivity,
    *,
    config: PolicyConfig | None = None,
    strict_mode: bool | None = None,
) -> tuple[DeploymentTier, list[str]]:
    """Raise PolicyViolationError when strict mode blocks a request."""
    policy = config or load_policy_config()
    deployment_tier, warnings = evaluate_model_policy(
        backend_name=backend_name,
        model_id=model_id,
        sensitivity=sensitivity,
        config=policy,
    )
    if effective_strict_mode(policy, strict_mode) and warnings:
        raise PolicyViolationError(" ".join(warnings))
    return deployment_tier, warnings


@lru_cache(maxsize=8)
def _load_policy_config_cached(path_key: str) -> PolicyConfig:
    if path_key:
        path = Path(path_key)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            return _policy_from_payload(payload)
    return PolicyConfig(
        strict_mode=False,
        max_tokens_per_run=None,
        approved_models={key: set(values) for key, values in _DEFAULT_APPROVED_MODELS.items()},
        presets=dict(_DEFAULT_PRESETS),
    )


def _policy_from_payload(payload: dict) -> PolicyConfig:
    strict_mode = bool(payload.get("strict_mode", False))
    max_tokens_per_run = payload.get("max_tokens_per_run")

    approved_raw = payload.get("approved_models", _DEFAULT_APPROVED_MODELS)
    approved_models = {
        backend: set(models)
        for backend, models in approved_raw.items()
    }

    presets_raw = payload.get("presets", {})
    presets: dict[str, ModelPreset] = {}
    for name, raw in presets_raw.items():
        presets[name] = ModelPreset(
            name=name,
            backend=raw["backend"],
            model=raw["model"],
            deployment_tier=DeploymentTier(raw["deployment_tier"]),
            description=raw.get("description", ""),
        )
    if not presets:
        presets = dict(_DEFAULT_PRESETS)

    return PolicyConfig(
        strict_mode=strict_mode,
        max_tokens_per_run=max_tokens_per_run,
        approved_models=approved_models,
        presets=presets,
    )


def _resolve_policy_path(path: str | Path | None) -> Path | None:
    if path is not None:
        return Path(path)
    env_path = os.environ.get("COBOL_INTEL_POLICY_PATH")
    if env_path:
        return Path(env_path)
    if _DEFAULT_POLICY_PATH.exists():
        return _DEFAULT_POLICY_PATH
    return None
