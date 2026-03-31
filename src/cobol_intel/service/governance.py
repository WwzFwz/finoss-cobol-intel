"""Governance utilities for sensitivity, redaction, and audit logging."""

from __future__ import annotations

import getpass
import re
from pathlib import Path

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut
from cobol_intel.contracts.governance import (
    AuditActor,
    AuditEvent,
    DataSensitivity,
    GovernanceSummary,
    TokenUsageSummary,
)
from cobol_intel.contracts.manifest import Manifest
from cobol_intel.contracts.governance import DeploymentTier
from cobol_intel.llm.policy import evaluate_model_policy
from cobol_intel.outputs import write_jsonl_artifact

_RESTRICTED_PATTERNS = (
    "account",
    "acct",
    "card",
    "pan",
    "ssn",
    "customer-name",
    "cust-name",
    "dob",
    "iban",
)
_HIGH_PATTERNS = (
    "balance",
    "salary",
    "address",
    "phone",
    "email",
    "customer",
)
_MODERATE_PATTERNS = (
    "amount",
    "payment",
    "invoice",
    "ledger",
    "interest",
    "loan",
)


def default_actor(channel: str = "cli") -> AuditActor:
    """Best-effort actor identity without a full auth system."""
    return AuditActor(actor_id=getpass.getuser() or "unknown", channel=channel)


def detect_ast_sensitivity(ast: ASTOutput) -> DataSensitivity:
    """Infer data sensitivity from COBOL field and paragraph names."""
    candidates: list[str] = [ast.program_id or "", ast.file_path, *ast.procedure_using]
    for item in ast.data_items:
        _collect_data_item_names(item, candidates)
    for paragraph in ast.paragraphs:
        candidates.append(paragraph.name)
        for statement in paragraph.statements:
            if statement.target:
                candidates.append(statement.target)
            if statement.condition:
                candidates.append(statement.condition)
            if statement.raw:
                candidates.append(statement.raw)
    normalized = " ".join(candidates).lower()

    if any(pattern in normalized for pattern in _RESTRICTED_PATTERNS):
        return DataSensitivity.RESTRICTED
    if any(pattern in normalized for pattern in _HIGH_PATTERNS):
        return DataSensitivity.HIGH
    if any(pattern in normalized for pattern in _MODERATE_PATTERNS):
        return DataSensitivity.MODERATE
    return DataSensitivity.LOW


def redact_prompt_text(text: str) -> str:
    """Mask obvious identifiers before sending content to cloud providers."""
    redacted = re.sub(r"\b\d{10,19}\b", "[REDACTED-NUMERIC-ID]", text)
    redacted = re.sub(r"\b[A-Z]{2,10}-ACCOUNT(?:-NO|-NUMBER)?\b", "[REDACTED-FIELD]", redacted)
    return redacted


def append_audit_event(log_path: Path, event: AuditEvent) -> Path:
    """Append one audit event to the JSONL log."""
    return write_jsonl_artifact(log_path, event)


def apply_llm_governance(
    manifest: Manifest,
    backend_name: str,
    model_id: str,
    sensitivity: DataSensitivity,
    total_tokens: int,
    redaction_applied: bool = False,
) -> GovernanceSummary:
    """Update manifest governance metadata after an explain run."""
    deployment_tier, warnings = evaluate_model_policy(backend_name, model_id, sensitivity)
    manifest.governance.data_sensitivity = sensitivity
    manifest.governance.approved_backend = backend_name
    manifest.governance.approved_model = model_id
    manifest.governance.deployment_tier = deployment_tier
    manifest.governance.redaction_applied = manifest.governance.redaction_applied or redaction_applied
    manifest.governance.policy_warnings.extend(warnings)
    manifest.governance.token_usage.requests += 1
    manifest.governance.token_usage.total_tokens += total_tokens
    for warning in warnings:
        if warning not in manifest.warnings:
            manifest.warnings.append(warning)
    return manifest.governance


def should_redact_prompts(backend_name: str, sensitivity: DataSensitivity) -> bool:
    """Cloud providers get redacted prompts for sensitive workloads."""
    deployment_tier, _ = evaluate_model_policy(backend_name, "", sensitivity)
    return deployment_tier == DeploymentTier.CLOUD and sensitivity in {
        DataSensitivity.HIGH,
        DataSensitivity.RESTRICTED,
    }


def initialize_audit_log(manifest: Manifest, run_dir: Path) -> Path:
    """Create and register the audit log path for a run."""
    rel_path = Path("logs") / "audit_events.jsonl"
    if rel_path.as_posix() not in manifest.artifacts.logs:
        manifest.artifacts.logs.append(rel_path.as_posix())
    return run_dir / rel_path


def _collect_data_item_names(item: DataItemOut, acc: list[str]) -> None:
    acc.append(item.name)
    if item.redefines:
        acc.append(item.redefines)
    for child in item.children:
        _collect_data_item_names(child, acc)
