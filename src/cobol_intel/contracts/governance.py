"""Governance and audit contracts for enterprise-safe LLM workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class DataSensitivity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    RESTRICTED = "restricted"


class DeploymentTier(str, Enum):
    CLOUD = "cloud"
    HYBRID = "hybrid"
    LOCAL_ONLY = "local_only"


class AuditActor(BaseModel):
    actor_id: str = "unknown"
    channel: str = "cli"


class AuditEvent(BaseModel):
    schema_version: str = SCHEMA_VERSION
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: str = ""
    actor: AuditActor = Field(default_factory=AuditActor)
    status: str = "success"
    backend: str | None = None
    model: str | None = None
    file_path: str | None = None
    program_id: str | None = None
    sensitivity: DataSensitivity | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TokenUsageSummary(BaseModel):
    requests: int = 0
    total_tokens: int = 0


class GovernanceSummary(BaseModel):
    data_sensitivity: DataSensitivity = DataSensitivity.LOW
    approved_backend: str | None = None
    approved_model: str | None = None
    deployment_tier: DeploymentTier = DeploymentTier.HYBRID
    strict_policy_enforced: bool = False
    redaction_applied: bool = False
    max_tokens_per_run: int | None = None
    budget_exhausted: bool = False
    policy_warnings: list[str] = Field(default_factory=list)
    token_usage: TokenUsageSummary = Field(default_factory=TokenUsageSummary)
