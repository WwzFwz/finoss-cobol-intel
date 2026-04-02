"""LLM explanation service that layers on top of static analysis artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.contracts.ast_output import ASTOutput
from cobol_intel.contracts.explanation_output import ExplanationMode, ExplanationOutput
from cobol_intel.contracts.governance import AuditEvent, DataSensitivity
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.manifest import ErrorCode, RunError, RunStatus
from cobol_intel.contracts.rules_output import RulesOutput
from cobol_intel.llm.backend import LLMBackend
from cobol_intel.llm.explainer import explain_program
from cobol_intel.llm.policy import (
    PolicyConfig,
    PolicyViolationError,
    effective_max_tokens_per_run,
    effective_strict_mode,
    enforce_model_policy,
    load_policy_config,
)
from cobol_intel.outputs import write_json_artifact, write_text_artifact
from cobol_intel.service.cache import ExplanationCache, make_cache_key
from cobol_intel.service.governance import (
    append_audit_event,
    apply_llm_governance,
    default_actor,
    detect_ast_sensitivity,
    initialize_audit_log,
    redact_prompt_text,
    should_redact_prompts,
)
from cobol_intel.service.parallel import ExplainJob, parallel_explain
from cobol_intel.service.pipeline import AnalysisRunResult, analyze_path, to_ast_output
from cobol_intel.service.run_metrics import build_run_metrics, write_run_metrics


@dataclass(frozen=True)
class _ExplainContext:
    result_index: int
    file_path: str
    program_id: str | None
    parser_name: str
    ast_output: ASTOutput
    rules_output: RulesOutput | None
    sensitivity: DataSensitivity
    redaction_applied: bool
    artifact_name: str
    cache_key: object | None


def explain_path(
    path: str | Path,
    backend: LLMBackend,
    mode: ExplanationMode = ExplanationMode.TECHNICAL,
    output_dir: str | Path = "artifacts",
    copybook_dirs: list[str | Path] | None = None,
    policy_config_path: str | Path | None = None,
    strict_policy: bool | None = None,
    max_tokens_per_run: int | None = None,
    parallel: bool = False,
    max_workers: int | None = None,
    use_cache: bool = True,
    cache_dir: str | Path | None = None,
) -> tuple[AnalysisRunResult, list[ExplanationOutput]]:
    """Analyze COBOL file(s) and generate traceable LLM explanations."""
    run_result = analyze_path(
        path=path,
        output_dir=output_dir,
        copybook_dirs=copybook_dirs,
    )

    explanations: list[ExplanationOutput] = []
    successful = [r for r in run_result.parse_results if r.success]
    call_graph = build_call_graph(successful)
    audit_log_path = initialize_audit_log(run_result.manifest, run_result.run_dir)
    policy_config = load_policy_config(policy_config_path)
    policy_config_json = _policy_config_json(policy_config)
    strict_policy_enabled = effective_strict_mode(policy_config, strict_policy)
    token_budget = effective_max_tokens_per_run(policy_config, max_tokens_per_run)
    cache = (
        ExplanationCache(Path(cache_dir) if cache_dir is not None else None)
        if use_cache
        else None
    )

    run_result.manifest.governance.strict_policy_enforced = strict_policy_enabled
    run_result.manifest.governance.max_tokens_per_run = token_budget

    consumed_tokens = 0
    retry_count = 0
    timeout_count = 0
    cache_hits = 0
    cache_misses = 0
    policy_violation_count = 0

    contexts = _build_contexts(
        successful,
        run_result.rules_outputs,
        call_graph,
        backend,
        mode,
        policy_config_json,
        run_result,
        use_cache,
    )

    if parallel and token_budget is not None:
        parallel = False
        warning = (
            "Parallel explain was disabled because token budget enforcement "
            "requires sequential execution."
        )
        run_result.manifest.warnings.append(warning)

    pending_contexts: list[_ExplainContext] = []
    for context in contexts:
        append_audit_event(
            audit_log_path,
            AuditEvent(
                event_type="llm.explain.started",
                run_id=run_result.manifest.run_id,
                actor=default_actor(),
                backend=backend.name,
                model=backend.model_id,
                file_path=context.file_path,
                program_id=context.program_id,
                sensitivity=context.sensitivity,
                details={"mode": mode.value},
            ),
        )
        try:
            enforce_model_policy(
                backend_name=backend.name,
                model_id=backend.model_id,
                sensitivity=context.sensitivity,
                config=policy_config,
                strict_mode=strict_policy_enabled,
            )
        except PolicyViolationError as exc:
            policy_violation_count += 1
            _record_failure(
                run_result,
                audit_log_path,
                backend,
                context,
                mode,
                exc,
                token_budget,
            )
            append_audit_event(
                audit_log_path,
                AuditEvent(
                    event_type="policy.blocked",
                    run_id=run_result.manifest.run_id,
                    actor=default_actor(),
                    status="failed",
                    backend=backend.name,
                    model=backend.model_id,
                    file_path=context.file_path,
                    program_id=context.program_id,
                    sensitivity=context.sensitivity,
                    details={"mode": mode.value, "reason": str(exc)},
                ),
            )
            continue

        if cache is not None and context.cache_key is not None:
            cached = cache.get(context.cache_key)
            if cached is not None:
                cache_hits += 1
                explanations.append(cached)
                _write_explanation_artifacts(run_result, context.artifact_name, cached)
                _record_success_events(
                    run_result=run_result,
                    audit_log_path=audit_log_path,
                    backend=backend,
                    context=context,
                    mode=mode,
                    explanation=cached,
                    token_budget=token_budget,
                    counted_tokens=0,
                    request_count=0,
                    cache_event="cache.hit",
                )
                continue

            cache_misses += 1
            append_audit_event(
                audit_log_path,
                AuditEvent(
                    event_type="cache.miss",
                    run_id=run_result.manifest.run_id,
                    actor=default_actor(),
                    status="miss",
                    backend=backend.name,
                    model=backend.model_id,
                    file_path=context.file_path,
                    program_id=context.program_id,
                    sensitivity=context.sensitivity,
                    details={"mode": mode.value},
                ),
            )

        if parallel:
            pending_contexts.append(context)
            continue

        if token_budget is not None and consumed_tokens >= token_budget:
            _record_budget_skip(
                run_result,
                audit_log_path,
                backend,
                context,
                consumed_tokens,
                token_budget,
            )
            break

        try:
            explanation = _generate_explanation(context, backend, call_graph, mode)
        except Exception as exc:
            _record_failure(
                run_result,
                audit_log_path,
                backend,
                context,
                mode,
                exc,
                token_budget,
            )
            continue

        explanations.append(explanation)
        counted_tokens = explanation.tokens_used
        consumed_tokens += counted_tokens
        retry_count += explanation.retry_count
        timeout_count += explanation.timeout_count
        if cache is not None and context.cache_key is not None:
            cache.put(context.cache_key, explanation)

        _write_explanation_artifacts(run_result, context.artifact_name, explanation)
        _record_success_events(
            run_result=run_result,
            audit_log_path=audit_log_path,
            backend=backend,
            context=context,
            mode=mode,
            explanation=explanation,
            token_budget=token_budget,
            counted_tokens=counted_tokens,
            request_count=1,
        )

        if token_budget is not None and consumed_tokens >= token_budget:
            _record_budget_reached(
                run_result,
                audit_log_path,
                backend,
                context,
                consumed_tokens,
                token_budget,
            )
            break

    if parallel and pending_contexts:
        jobs = [
            ExplainJob(
                index=index,
                ast=context.ast_output,
                rules=context.rules_output,
                prompt_transform=redact_prompt_text if context.redaction_applied else None,
            )
            for index, context in enumerate(pending_contexts)
        ]
        for position, result in enumerate(
            parallel_explain(
                jobs,
                backend,
                call_graph=call_graph,
                mode=mode,
                max_workers=max_workers,
            )
        ):
            context = pending_contexts[position]
            if result.error is not None:
                _record_failure(
                    run_result,
                    audit_log_path,
                    backend,
                    context,
                    mode,
                    result.error,
                    token_budget,
                )
                continue

            explanation = result.explanation
            assert explanation is not None
            explanations.append(explanation)
            consumed_tokens += explanation.tokens_used
            retry_count += explanation.retry_count
            timeout_count += explanation.timeout_count
            if cache is not None and context.cache_key is not None:
                cache.put(context.cache_key, explanation)

            _write_explanation_artifacts(run_result, context.artifact_name, explanation)
            _record_success_events(
                run_result=run_result,
                audit_log_path=audit_log_path,
                backend=backend,
                context=context,
                mode=mode,
                explanation=explanation,
                token_budget=token_budget,
                counted_tokens=explanation.tokens_used,
                request_count=1,
            )

    run_result.manifest.finished_at = datetime.now(timezone.utc)
    if run_result.manifest.errors:
        run_result.manifest.status = _final_explain_status(run_result, explanations)

    metrics = build_run_metrics(
        run_result.manifest,
        phase="explain",
        files_total=len(run_result.parse_results),
        files_successful=len(successful),
        files_failed=len(run_result.parse_results) - len(successful),
        backend=backend.name,
        model=backend.model_id,
        retry_count=retry_count,
        timeout_count=timeout_count,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        token_usage_total=consumed_tokens,
        policy_violation_count=policy_violation_count,
        budget_exhausted=run_result.manifest.governance.budget_exhausted,
    )
    write_run_metrics(run_result.run_dir, run_result.manifest, metrics)
    write_json_artifact(run_result.run_dir / "manifest.json", run_result.manifest)

    return run_result, explanations


def _build_contexts(
    successful_results: list,
    rules_outputs: list[RulesOutput],
    call_graph: CallGraphOutput,
    backend: LLMBackend,
    mode: ExplanationMode,
    policy_config_json: str,
    run_result: AnalysisRunResult,
    use_cache: bool,
) -> list[_ExplainContext]:
    contexts: list[_ExplainContext] = []
    for index, result in enumerate(successful_results):
        ast_output = to_ast_output(result, file_path=result.file_path)
        rules_output = rules_outputs[index] if index < len(rules_outputs) else None
        sensitivity = detect_ast_sensitivity(ast_output)
        redaction_applied = should_redact_prompts(
            backend.name,
            sensitivity,
        )
        cache_key = None
        if use_cache:
            source_text = Path(result.file_path).read_text(encoding="utf-8")
            cache_key = make_cache_key(
                source_text=source_text,
                analysis_payload_json=_analysis_payload_json(
                    ast_output,
                    rules_output,
                    call_graph,
                ),
                parser_version=result.parser_name,
                policy_config_json=policy_config_json,
                backend=backend.name,
                model=backend.model_id,
                mode=mode.value,
                tool_version=run_result.manifest.tool_version,
            )

        contexts.append(
            _ExplainContext(
                result_index=index,
                file_path=result.file_path,
                program_id=result.program_id,
                parser_name=result.parser_name,
                ast_output=ast_output,
                rules_output=rules_output,
                sensitivity=sensitivity,
                redaction_applied=redaction_applied,
                artifact_name=_slugify(result.program_id or Path(result.file_path).stem),
                cache_key=cache_key,
            )
        )
    return contexts


def _generate_explanation(
    context: _ExplainContext,
    backend: LLMBackend,
    call_graph: CallGraphOutput,
    mode: ExplanationMode,
) -> ExplanationOutput:
    return explain_program(
        backend=backend,
        ast=context.ast_output,
        rules=context.rules_output,
        call_graph=call_graph,
        mode=mode,
        prompt_transform=redact_prompt_text if context.redaction_applied else None,
    )


def _record_success_events(
    *,
    run_result: AnalysisRunResult,
    audit_log_path: Path,
    backend: LLMBackend,
    context: _ExplainContext,
    mode: ExplanationMode,
    explanation: ExplanationOutput,
    token_budget: int | None,
    counted_tokens: int,
    request_count: int,
    cache_event: str | None = None,
) -> None:
    apply_llm_governance(
        run_result.manifest,
        backend_name=backend.name,
        model_id=backend.model_id,
        sensitivity=context.sensitivity,
        total_tokens=counted_tokens,
        request_count=request_count,
        redaction_applied=context.redaction_applied,
        strict_policy_enforced=run_result.manifest.governance.strict_policy_enforced,
        max_tokens_per_run=token_budget,
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
            file_path=context.file_path,
            program_id=context.program_id,
            sensitivity=context.sensitivity,
            details={
                "tokens_used": counted_tokens,
                "mode": mode.value,
                "redaction_applied": context.redaction_applied,
                "token_budget": token_budget,
                "cache_event": cache_event,
            },
        ),
    )
    if cache_event is not None:
        append_audit_event(
            audit_log_path,
            AuditEvent(
                event_type=cache_event,
                run_id=run_result.manifest.run_id,
                actor=default_actor(),
                status="success",
                backend=backend.name,
                model=backend.model_id,
                file_path=context.file_path,
                program_id=context.program_id,
                sensitivity=context.sensitivity,
                details={"mode": mode.value},
            ),
        )
    if explanation.retry_count > 0:
        append_audit_event(
            audit_log_path,
            AuditEvent(
                event_type="backend.retry",
                run_id=run_result.manifest.run_id,
                actor=default_actor(),
                status="warning",
                backend=backend.name,
                model=backend.model_id,
                file_path=context.file_path,
                program_id=context.program_id,
                sensitivity=context.sensitivity,
                details={"count": explanation.retry_count, "mode": mode.value},
            ),
        )
    if explanation.timeout_count > 0:
        append_audit_event(
            audit_log_path,
            AuditEvent(
                event_type="backend.timeout",
                run_id=run_result.manifest.run_id,
                actor=default_actor(),
                status="warning",
                backend=backend.name,
                model=backend.model_id,
                file_path=context.file_path,
                program_id=context.program_id,
                sensitivity=context.sensitivity,
                details={"count": explanation.timeout_count, "mode": mode.value},
            ),
        )


def _record_failure(
    run_result: AnalysisRunResult,
    audit_log_path: Path,
    backend: LLMBackend,
    context: _ExplainContext,
    mode: ExplanationMode,
    exc: Exception,
    token_budget: int | None,
) -> None:
    if isinstance(exc, PolicyViolationError):
        error_code = ErrorCode.POLICY_VIOLATION
        module_name = "policy"
    elif "timeout" in str(exc).lower():
        error_code = ErrorCode.LLM_TIMEOUT
        module_name = "llm"
    else:
        error_code = ErrorCode.LLM_BACKEND
        module_name = "llm"
    run_result.manifest.errors.append(
        RunError(
            file=context.file_path,
            code=error_code,
            module=module_name,
            message=str(exc),
        )
    )
    run_result.manifest.warnings.append(
        f"{module_name.upper()} explanation failed for {context.file_path}: {exc}"
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
            file_path=context.file_path,
            program_id=context.program_id,
            sensitivity=context.sensitivity,
            details={
                "error": str(exc),
                "mode": mode.value,
                "token_budget": token_budget,
            },
        ),
    )


def _record_budget_skip(
    run_result: AnalysisRunResult,
    audit_log_path: Path,
    backend: LLMBackend,
    context: _ExplainContext,
    consumed_tokens: int,
    token_budget: int,
) -> None:
    run_result.manifest.governance.budget_exhausted = True
    message = (
        f"Token budget exhausted before explaining {context.file_path}: "
        f"{consumed_tokens}/{token_budget} tokens used."
    )
    run_result.manifest.warnings.append(message)
    run_result.manifest.errors.append(
        RunError(
            file=context.file_path,
            code=ErrorCode.LLM_BUDGET,
            module="budget",
            message=message,
        )
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
            file_path=context.file_path,
            program_id=context.program_id,
            sensitivity=context.sensitivity,
            details={"tokens_used": consumed_tokens, "token_budget": token_budget},
        ),
    )


def _record_budget_reached(
    run_result: AnalysisRunResult,
    audit_log_path: Path,
    backend: LLMBackend,
    context: _ExplainContext,
    consumed_tokens: int,
    token_budget: int,
) -> None:
    run_result.manifest.governance.budget_exhausted = True
    budget_message = (
        f"Token budget reached after {context.file_path}: "
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
            file_path=context.file_path,
            program_id=context.program_id,
            sensitivity=context.sensitivity,
            details={"tokens_used": consumed_tokens, "token_budget": token_budget},
        ),
    )


def _write_explanation_artifacts(
    run_result: AnalysisRunResult,
    artifact_name: str,
    explanation: ExplanationOutput,
) -> None:
    json_rel = Path("docs") / f"{artifact_name}_explanation.json"
    write_json_artifact(run_result.run_dir / json_rel, explanation)
    if json_rel.as_posix() not in run_result.manifest.artifacts.docs:
        run_result.manifest.artifacts.docs.append(json_rel.as_posix())

    md_rel = Path("docs") / f"{artifact_name}_explanation.md"
    write_text_artifact(
        run_result.run_dir / md_rel,
        _render_explanation_md(explanation),
    )
    if md_rel.as_posix() not in run_result.manifest.artifacts.docs:
        run_result.manifest.artifacts.docs.append(md_rel.as_posix())


def _analysis_payload_json(
    ast_output: ASTOutput,
    rules_output: RulesOutput | None,
    call_graph: CallGraphOutput | None,
) -> str:
    payload = {
        "ast": ast_output.model_dump(mode="json"),
        "rules": rules_output.model_dump(mode="json") if rules_output else None,
        "call_graph": call_graph.model_dump(mode="json") if call_graph else None,
    }
    return json.dumps(payload, sort_keys=True)


def _policy_config_json(config: PolicyConfig) -> str:
    payload = {
        "strict_mode": config.strict_mode,
        "max_tokens_per_run": config.max_tokens_per_run,
        "approved_models": {
            backend: sorted(models)
            for backend, models in sorted(config.approved_models.items())
        },
        "presets": {
            name: {
                "backend": preset.backend,
                "model": preset.model,
                "deployment_tier": preset.deployment_tier.value,
                "description": preset.description,
            }
            for name, preset in sorted(config.presets.items())
        },
    }
    return json.dumps(payload, sort_keys=True)


def _render_explanation_md(explanation: ExplanationOutput) -> str:
    """Render explanation as readable Markdown."""
    lines = [
        f"# Explanation - {explanation.program_id or 'UNKNOWN'}",
        (
            f"Mode: {explanation.mode.value} | Backend: {explanation.backend} | "
            f"Model: {explanation.model}"
        ),
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
