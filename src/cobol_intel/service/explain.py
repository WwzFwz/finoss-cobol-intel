"""LLM explanation service — runs Phase 1 analysis + LLM explanation."""

from __future__ import annotations

from pathlib import Path

from cobol_intel.contracts.explanation_output import ExplanationMode, ExplanationOutput
from cobol_intel.contracts.governance import AuditEvent
from cobol_intel.contracts.manifest import ErrorCode, RunError, RunStatus
from cobol_intel.llm.backend import LLMBackend
from cobol_intel.llm.explainer import explain_program
from cobol_intel.llm.policy import (
    PolicyViolationError,
    effective_max_tokens_per_run,
    effective_strict_mode,
    enforce_model_policy,
    load_policy_config,
)
from cobol_intel.outputs import write_json_artifact, write_text_artifact
from cobol_intel.service.governance import (
    append_audit_event,
    apply_llm_governance,
    default_actor,
    detect_ast_sensitivity,
    initialize_audit_log,
    redact_prompt_text,
    should_redact_prompts,
)
from cobol_intel.service.pipeline import AnalysisRunResult, analyze_path, to_ast_output


def explain_path(
    path: str | Path,
    backend: LLMBackend,
    mode: ExplanationMode = ExplanationMode.TECHNICAL,
    output_dir: str | Path = "artifacts",
    copybook_dirs: list[str | Path] | None = None,
    policy_config_path: str | Path | None = None,
    strict_policy: bool | None = None,
    max_tokens_per_run: int | None = None,
) -> tuple[AnalysisRunResult, list[ExplanationOutput]]:
    """Analyze COBOL file(s) and generate LLM explanations.

    Runs the Phase 1 pipeline first, then explains each successfully
    parsed program using the provided LLM backend.

    Returns:
        Tuple of (AnalysisRunResult, list of ExplanationOutput).
    """
    # Phase 1: static analysis
    run_result = analyze_path(
        path=path,
        output_dir=output_dir,
        copybook_dirs=copybook_dirs,
    )

    explanations: list[ExplanationOutput] = []
    successful = [r for r in run_result.parse_results if r.success]
    audit_log_path = initialize_audit_log(run_result.manifest, run_result.run_dir)
    policy_config = load_policy_config(policy_config_path)
    strict_policy_enabled = effective_strict_mode(policy_config, strict_policy)
    token_budget = effective_max_tokens_per_run(policy_config, max_tokens_per_run)
    run_result.manifest.governance.strict_policy_enforced = strict_policy_enabled
    run_result.manifest.governance.max_tokens_per_run = token_budget
    consumed_tokens = 0

    # Build call graph reference (already computed, extract from artifact)
    from cobol_intel.analysis.call_graph import build_call_graph
    call_graph = build_call_graph(successful)

    for i, result in enumerate(successful):
        if token_budget is not None and consumed_tokens >= token_budget:
            run_result.manifest.governance.budget_exhausted = True
            message = (
                f"Token budget exhausted before explaining {result.file_path}: "
                f"{consumed_tokens}/{token_budget} tokens used."
            )
            run_result.manifest.warnings.append(message)
            run_result.manifest.errors.append(
                RunError(file=result.file_path, code=ErrorCode.LLM_BUDGET, module="budget", message=message)
            )
            append_audit_event(
                audit_log_path,
                AuditEvent(
                    event_type="llm.explain.skipped_budget",
                    run_id=run_result.manifest.run_id,
                    actor=default_actor(),
                    status="skipped",
                    backend=backend.name,
                    model=backend.model_id,
                    file_path=result.file_path,
                    program_id=result.program_id,
                    details={
                        "tokens_used": consumed_tokens,
                        "token_budget": token_budget,
                    },
                ),
            )
            break

        ast_output = to_ast_output(result, file_path=result.file_path)
        rules_output = run_result.rules_outputs[i] if i < len(run_result.rules_outputs) else None
        sensitivity = detect_ast_sensitivity(ast_output)
        redaction_applied = should_redact_prompts(
            backend.name,
            sensitivity,
            config=policy_config,
        )
        append_audit_event(
            audit_log_path,
            AuditEvent(
                event_type="llm.explain.started",
                run_id=run_result.manifest.run_id,
                actor=default_actor(),
                backend=backend.name,
                model=backend.model_id,
                file_path=result.file_path,
                program_id=result.program_id,
                sensitivity=sensitivity,
                details={"mode": mode.value},
            ),
        )

        try:
            enforce_model_policy(
                backend_name=backend.name,
                model_id=backend.model_id,
                sensitivity=sensitivity,
                config=policy_config,
                strict_mode=strict_policy_enabled,
            )
            explanation = explain_program(
                backend=backend,
                ast=ast_output,
                rules=rules_output,
                call_graph=call_graph,
                mode=mode,
                prompt_transform=redact_prompt_text if redaction_applied else None,
            )
            explanations.append(explanation)
            consumed_tokens += explanation.tokens_used

            artifact_name = _slugify(result.program_id or Path(result.file_path).stem)
            json_rel = Path("docs") / f"{artifact_name}_explanation.json"
            write_json_artifact(run_result.run_dir / json_rel, explanation)
            run_result.manifest.artifacts.docs.append(json_rel.as_posix())

            md_rel = Path("docs") / f"{artifact_name}_explanation.md"
            write_text_artifact(run_result.run_dir / md_rel, _render_explanation_md(explanation))
            run_result.manifest.artifacts.docs.append(md_rel.as_posix())
            apply_llm_governance(
                run_result.manifest,
                backend_name=backend.name,
                model_id=backend.model_id,
                sensitivity=sensitivity,
                total_tokens=explanation.tokens_used,
                redaction_applied=redaction_applied,
                strict_policy_enforced=strict_policy_enabled,
                max_tokens_per_run=token_budget,
                config=policy_config,
            )
            append_audit_event(
                audit_log_path,
                AuditEvent(
                    event_type="llm.explain.completed",
                    run_id=run_result.manifest.run_id,
                    actor=default_actor(),
                    status="success",
                    backend=backend.name,
                    model=backend.model_id,
                    file_path=result.file_path,
                    program_id=result.program_id,
                    sensitivity=sensitivity,
                    details={
                        "tokens_used": explanation.tokens_used,
                        "mode": mode.value,
                        "redaction_applied": redaction_applied,
                        "token_budget": token_budget,
                    },
                ),
            )
            if token_budget is not None and consumed_tokens >= token_budget:
                run_result.manifest.governance.budget_exhausted = True
                budget_message = (
                    f"Token budget reached after {result.file_path}: "
                    f"{consumed_tokens}/{token_budget} tokens used. "
                    "Additional explanations were skipped."
                )
                run_result.manifest.warnings.append(budget_message)
                append_audit_event(
                    audit_log_path,
                    AuditEvent(
                        event_type="llm.explain.budget_reached",
                        run_id=run_result.manifest.run_id,
                        actor=default_actor(),
                        status="warning",
                        backend=backend.name,
                        model=backend.model_id,
                        file_path=result.file_path,
                        program_id=result.program_id,
                        details={
                            "tokens_used": consumed_tokens,
                            "token_budget": token_budget,
                        },
                    ),
                )
                break
        except Exception as exc:
            if isinstance(exc, PolicyViolationError):
                error_code = ErrorCode.POLICY_VIOLATION
                module_name = "policy"
            else:
                error_code = ErrorCode.LLM_BACKEND
                module_name = "llm"
            run_result.manifest.errors.append(
                RunError(
                    file=result.file_path,
                    code=error_code,
                    module=module_name,
                    message=str(exc),
                )
            )
            run_result.manifest.warnings.append(
                f"{module_name.upper()} explanation failed for {result.file_path}: {exc}"
            )
            append_audit_event(
                audit_log_path,
                AuditEvent(
                    event_type="llm.explain.failed",
                    run_id=run_result.manifest.run_id,
                    actor=default_actor(),
                    status="failed",
                    backend=backend.name,
                    model=backend.model_id,
                    file_path=result.file_path,
                    program_id=result.program_id,
                    sensitivity=sensitivity,
                    details={"error": str(exc), "mode": mode.value, "token_budget": token_budget},
                ),
            )

    if run_result.manifest.errors:
        run_result.manifest.status = _final_explain_status(run_result, explanations)

    write_json_artifact(run_result.run_dir / "manifest.json", run_result.manifest)

    return run_result, explanations


def _render_explanation_md(explanation: ExplanationOutput) -> str:
    """Render explanation as readable Markdown."""
    lines = [
        f"# Explanation - {explanation.program_id or 'UNKNOWN'}",
        f"Mode: {explanation.mode.value} | Backend: {explanation.backend} | Model: {explanation.model}",
        "",
    ]

    if explanation.program_summary:
        lines.extend(["## Program Summary", "", explanation.program_summary, ""])

    if explanation.data_summary:
        lines.extend(["## Data Structures", "", explanation.data_summary, ""])

    if explanation.business_rules_summary:
        lines.extend(["## Business Rules", "", explanation.business_rules_summary, ""])

    if explanation.paragraph_explanations:
        lines.extend(["## Paragraph Details", ""])
        for para_exp in explanation.paragraph_explanations:
            lines.append(f"### {para_exp.paragraph}")
            lines.append(para_exp.summary)
            if para_exp.source:
                lines.append(f"*Source: {para_exp.source.file}*")
            lines.append("")

    lines.append(f"---\nTokens used: {explanation.tokens_used}")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    chars = [c.lower() if c.isalnum() else "_" for c in value.strip()]
    collapsed = "".join(chars)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed.strip("_") or "unknown"


def _final_explain_status(
    run_result: AnalysisRunResult,
    explanations: list[ExplanationOutput],
) -> RunStatus:
    """Adjust manifest status after LLM phase finishes with partial failures."""
    if explanations:
        return RunStatus.PARTIALLY_COMPLETED
    if any(result.success for result in run_result.parse_results):
        return RunStatus.PARTIALLY_COMPLETED
    return RunStatus.FAILED
