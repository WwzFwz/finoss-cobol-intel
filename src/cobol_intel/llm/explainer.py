"""Explanation engine — orchestrates context building and LLM generation.

Produces ExplanationOutput with traceability back to source artifacts.
"""

from __future__ import annotations

from collections.abc import Callable

from cobol_intel.contracts.ast_output import ASTOutput
from cobol_intel.contracts.explanation_output import (
    ExplanationMode,
    ExplanationOutput,
    ParagraphExplanation,
)
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.rules_output import RulesOutput
from cobol_intel.contracts.source_ref import SourceRef
from cobol_intel.llm.backend import LLMBackend
from cobol_intel.llm.context_builder import (
    build_paragraph_prompt,
    build_program_prompt,
    build_system_prompt,
)

_DEFAULT_MAX_PARAGRAPH_EXPLANATIONS = 8


def explain_program(
    backend: LLMBackend,
    ast: ASTOutput,
    rules: RulesOutput | None = None,
    call_graph: CallGraphOutput | None = None,
    mode: ExplanationMode = ExplanationMode.TECHNICAL,
    max_paragraph_explanations: int = _DEFAULT_MAX_PARAGRAPH_EXPLANATIONS,
    prompt_transform: Callable[[str], str] | None = None,
) -> ExplanationOutput:
    """Generate a full program explanation using the LLM backend.

    Steps:
    1. Build system prompt for the chosen mode
    2. Build program-level prompt from artifacts
    3. Call backend for program summary
    4. For each paragraph, build focused prompt and get explanation
    5. Assemble ExplanationOutput with traceability
    """
    system_prompt = build_system_prompt(mode)
    program_prompt = build_program_prompt(ast, rules, call_graph)

    # Program-level summary
    summary_prompt = (
        f"{program_prompt}\n\n"
        "---\n"
        "Based on the artifacts above, provide:\n"
        "1. A concise summary of what this program does (2-3 sentences)\n"
        "2. A summary of the key data structures\n"
        "3. A summary of the business rules\n\n"
        "Use the section headers: ## Program Summary, ## Data Structures, ## Business Rules"
    )
    if prompt_transform:
        summary_prompt = prompt_transform(summary_prompt)
    summary_response = backend.generate(summary_prompt, system=system_prompt)
    total_tokens = summary_response.total_tokens
    total_retries = summary_response.retry_count
    total_timeouts = summary_response.timeout_count

    # Parse sections from response
    program_summary, data_summary, rules_summary = _parse_summary_sections(
        summary_response.text
    )

    # Per-paragraph explanations
    selected_paragraphs, skipped_paragraphs = _select_paragraphs_for_explanation(
        ast,
        rules,
        max_paragraph_explanations,
    )
    paragraph_explanations: list[ParagraphExplanation] = []
    for para in selected_paragraphs:
        para_prompt = build_paragraph_prompt(ast, para.name, rules)
        if para_prompt is None:
            continue

        para_prompt += (
            "\n\n---\n"
            f"Explain what the paragraph '{para.name}' does. "
            "Be specific about conditions, data movements, and calls. "
            "Keep it concise (3-5 sentences)."
        )
        if prompt_transform:
            para_prompt = prompt_transform(para_prompt)
        para_response = backend.generate(para_prompt, system=system_prompt)
        total_tokens += para_response.total_tokens
        total_retries += para_response.retry_count
        total_timeouts += para_response.timeout_count

        paragraph_explanations.append(ParagraphExplanation(
            paragraph=para.name,
            summary=para_response.text.strip(),
            source=SourceRef(
                file=ast.file_path,
                paragraph=para.name,
            ),
        ))

    return ExplanationOutput(
        program_id=ast.program_id,
        file_path=ast.file_path,
        mode=mode,
        backend=backend.name,
        model=backend.model_id,
        program_summary=program_summary,
        program_summary_sources=_build_program_summary_sources(ast, selected_paragraphs),
        paragraph_explanations=paragraph_explanations,
        data_summary=data_summary,
        data_summary_sources=_build_data_summary_sources(ast),
        business_rules_summary=rules_summary,
        business_rules_summary_sources=_build_rules_summary_sources(ast, rules),
        paragraph_limit=max_paragraph_explanations,
        paragraphs_skipped=skipped_paragraphs,
        tokens_used=total_tokens,
        retry_count=total_retries,
        timeout_count=total_timeouts,
    )


def _parse_summary_sections(text: str) -> tuple[str, str, str]:
    """Parse program summary, data summary, and rules summary from LLM response."""
    sections: dict[str, list[str]] = {"program": [], "data": [], "rules": []}
    current = "program"

    for line in text.split("\n"):
        lower = line.strip().lower()
        if lower.startswith("## program summary"):
            current = "program"
        elif lower.startswith("## data structure"):
            current = "data"
        elif lower.startswith("## business rule"):
            current = "rules"
        else:
            sections[current].append(line)

    return (
        "\n".join(sections["program"]).strip(),
        "\n".join(sections["data"]).strip(),
        "\n".join(sections["rules"]).strip(),
    )


def _select_paragraphs_for_explanation(
    ast: ASTOutput,
    rules: RulesOutput | None,
    max_paragraph_explanations: int,
) -> tuple[list, list[str]]:
    """Pick the most valuable paragraphs to explain under a hard cap."""
    if max_paragraph_explanations <= 0:
        return [], [paragraph.name for paragraph in ast.paragraphs]
    if len(ast.paragraphs) <= max_paragraph_explanations:
        return list(ast.paragraphs), []

    rule_paragraphs = {
        rule.paragraph
        for rule in (rules.rules if rules else [])
        if rule.paragraph
    }
    ranked: list[tuple[int, int, object]] = []
    for index, paragraph in enumerate(ast.paragraphs):
        score = 0
        if paragraph.name in rule_paragraphs:
            score += 3
        stmt_types = {statement.type for statement in paragraph.statements}
        if stmt_types & {
            "IF",
            "EVALUATE",
            "CALL",
            "EXEC-SQL",
            "EXEC-CICS",
            "READ",
            "WRITE",
            "REWRITE",
        }:
            score += 2
        if stmt_types & {"PERFORM", "PERFORM-VARYING", "PERFORM-THRU"}:
            score += 1
        ranked.append((-score, index, paragraph))

    ranked.sort()
    selected = [paragraph for _, _, paragraph in ranked[:max_paragraph_explanations]]
    selected_names = {paragraph.name for paragraph in selected}
    selected = [paragraph for paragraph in ast.paragraphs if paragraph.name in selected_names]
    skipped = [
        paragraph.name
        for paragraph in ast.paragraphs
        if paragraph.name not in selected_names
    ]
    return selected, skipped


def _build_program_summary_sources(ast: ASTOutput, selected_paragraphs: list) -> list[SourceRef]:
    """Use selected paragraphs as the traceability anchor for the top summary."""
    if selected_paragraphs:
        return [
            SourceRef(file=ast.file_path, paragraph=paragraph.name)
            for paragraph in selected_paragraphs
        ]
    if ast.file_path:
        return [SourceRef(file=ast.file_path)]
    return []


def _build_data_summary_sources(ast: ASTOutput) -> list[SourceRef]:
    """Data summary points back to the source file for now."""
    if ast.file_path:
        return [SourceRef(file=ast.file_path)]
    return []


def _build_rules_summary_sources(ast: ASTOutput, rules: RulesOutput | None) -> list[SourceRef]:
    """Rules summary points to paragraphs where rules were extracted."""
    if rules and rules.rules:
        refs: list[SourceRef] = []
        seen: set[tuple[str, str | None]] = set()
        for rule in rules.rules:
            key = (ast.file_path, rule.paragraph)
            if key in seen:
                continue
            seen.add(key)
            refs.append(SourceRef(file=ast.file_path, paragraph=rule.paragraph))
        return refs
    if ast.file_path:
        return [SourceRef(file=ast.file_path)]
    return []
