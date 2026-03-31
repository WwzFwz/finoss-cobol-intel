"""Unit tests for governance helpers used by the service layer."""

import shutil
from pathlib import Path

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut
from cobol_intel.contracts.governance import AuditEvent, DataSensitivity
from cobol_intel.contracts.manifest import Manifest, RunStatus
from cobol_intel.service.governance import (
    append_audit_event,
    apply_llm_governance,
    detect_ast_sensitivity,
    redact_prompt_text,
)

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "tests_runtime_governance"


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def test_detect_ast_sensitivity_marks_restricted_fields():
    ast = ASTOutput(
        program_id="ACCOUNTS",
        file_path="accounts.cbl",
        parser_name="antlr4",
        data_items=[DataItemOut(level=1, name="CUSTOMER-ACCOUNT-NUMBER")],
        paragraphs=[ParagraphOut(name="MAIN-LOGIC")],
    )
    assert detect_ast_sensitivity(ast) == DataSensitivity.RESTRICTED


def test_append_audit_event_writes_jsonl_line():
    log_path = RUNTIME_DIR / "audit_events.jsonl"
    append_audit_event(log_path, AuditEvent(event_type="analysis.run.started", run_id="run_1"))
    content = log_path.read_text(encoding="utf-8")
    assert "analysis.run.started" in content


def test_apply_llm_governance_updates_manifest():
    manifest = Manifest(
        tool_version="0.1.0",
        run_id="run_1",
        project_name="demo",
        status=RunStatus.RUNNING,
        started_at="2026-04-01T00:00:00Z",
        input_paths=["samples/demo.cbl"],
    )
    governance = apply_llm_governance(
        manifest,
        backend_name="ollama",
        model_id="llama3.1:8b",
        sensitivity=DataSensitivity.RESTRICTED,
        total_tokens=321,
        strict_policy_enforced=True,
        max_tokens_per_run=500,
    )
    assert governance.approved_backend == "ollama"
    assert governance.token_usage.total_tokens == 321
    assert manifest.governance.data_sensitivity == DataSensitivity.RESTRICTED
    assert manifest.governance.strict_policy_enforced is True
    assert manifest.governance.max_tokens_per_run == 500


def test_redact_prompt_text_masks_common_pii_markers():
    redacted = redact_prompt_text(
        "CUSTOMER-NAME john@example.com 123-45-6789 6281234567890 CUSTOMER-ACCOUNT-NUMBER"
    )
    assert "[REDACTED-FIELD]" in redacted
    assert "[REDACTED-EMAIL]" in redacted
    assert "[REDACTED-SSN]" in redacted
