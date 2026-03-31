"""Context builder — transforms Phase 1 artifacts into LLM-ready prompts.

Takes AST, business rules, and call graph data and builds structured prompts
tuned for technical, business, or audit explanation modes.
Includes smart chunking by paragraph/section to stay within token budgets.
"""

from __future__ import annotations

from cobol_intel.contracts.ast_output import ASTOutput
from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.rules_output import RulesOutput


_DEFAULT_MAX_CONTEXT_CHARS = 28_000  # ~8k tokens for context


def build_system_prompt(mode: ExplanationMode) -> str:
    """Build a system prompt appropriate for the explanation mode."""
    base = (
        "You are a COBOL legacy systems expert helping modernize financial software. "
        "You are given structured analysis artifacts (AST, business rules, call graph) "
        "extracted from a COBOL program by a static analysis pipeline. "
        "Use these artifacts to explain the program accurately. "
        "Always reference specific paragraphs, data items, and conditions from the artifacts."
    )

    mode_instructions = {
        ExplanationMode.TECHNICAL: (
            "\n\nFocus on TECHNICAL details:\n"
            "- Control flow and paragraph execution order\n"
            "- Data structures, PIC clauses, COMP-3 packed decimal usage\n"
            "- CALL dependencies and external program interfaces\n"
            "- REDEFINES, OCCURS, array access patterns\n"
            "- Potential issues: missing error handling, implicit type conversions"
        ),
        ExplanationMode.BUSINESS: (
            "\n\nFocus on BUSINESS LOGIC:\n"
            "- What business process does this program implement?\n"
            "- What are the decision rules (IF/EVALUATE conditions)?\n"
            "- What are the 88-level condition names and their business meaning?\n"
            "- What data flows in and out?\n"
            "- Explain in terms a business analyst or product manager would understand\n"
            "- Avoid COBOL-specific jargon where possible"
        ),
        ExplanationMode.AUDIT: (
            "\n\nFocus on AUDIT and COMPLIANCE:\n"
            "- What financial calculations are performed?\n"
            "- What validation rules exist and are they sufficient?\n"
            "- Are there hardcoded values that should be configurable?\n"
            "- What error conditions are handled vs unhandled?\n"
            "- What data items hold sensitive information (account numbers, balances)?\n"
            "- Flag any logic that could lead to regulatory risk"
        ),
    }

    return base + mode_instructions[mode]


def build_program_prompt(
    ast: ASTOutput,
    rules: RulesOutput | None = None,
    call_graph: CallGraphOutput | None = None,
    max_context_chars: int = _DEFAULT_MAX_CONTEXT_CHARS,
) -> str:
    """Build the main user prompt from Phase 1 artifacts.

    Chunks content to fit within max_context_chars budget.
    """
    sections: list[str] = []

    # Header
    header_lines = [
        f"# Program: {ast.program_id or 'UNKNOWN'}",
        f"File: {ast.file_path}",
        f"Parser: {ast.parser_name}",
    ]
    if ast.procedure_using:
        header_lines.append(
            f"PROCEDURE DIVISION USING: {', '.join(ast.procedure_using)}"
        )
    header_lines.append("")
    sections.append("\n".join(header_lines))

    if rules and rules.rules:
        rules_section = _build_rules_section(rules)
        sections.append(rules_section)

    if call_graph and call_graph.edges:
        graph_section = _build_graph_section(call_graph, ast.program_id)
        sections.append(graph_section)

    if ast.copybooks_used:
        sections.append(f"## Copybooks Used\n{', '.join(ast.copybooks_used)}\n")

    # Data items summary
    data_section = _build_data_section(ast)
    para_section = _build_paragraphs_section(ast)
    return _compose_prompt_with_budget(
        high_priority_sections=sections,
        data_section=data_section,
        paragraph_section=para_section,
        max_context_chars=max_context_chars,
    )


def build_paragraph_prompt(
    ast: ASTOutput,
    paragraph_name: str,
    rules: RulesOutput | None = None,
) -> str | None:
    """Build a focused prompt for explaining a single paragraph.

    Returns None if the paragraph is not found in the AST.
    """
    target_para = None
    for para in ast.paragraphs:
        if para.name == paragraph_name:
            target_para = para
            break
    if target_para is None:
        return None

    lines = [
        f"# Paragraph: {paragraph_name}",
        f"Program: {ast.program_id or 'UNKNOWN'}",
        "",
        "## Statements",
    ]

    for stmt in target_para.statements:
        lines.append(_format_statement(stmt, indent=0))

    # Include relevant rules
    if rules:
        relevant = [r for r in rules.rules if r.paragraph == paragraph_name]
        if relevant:
            lines.append("\n## Business Rules in This Paragraph")
            for rule in relevant:
                lines.append(f"- {rule.rule_id} ({rule.type}): `{rule.condition}`")
                if rule.actions:
                    lines.append(f"  Actions: {', '.join(rule.actions)}")

    return "\n".join(lines)


def _build_data_section(ast: ASTOutput) -> str:
    """Build data items section of the prompt."""
    lines = ["## Data Items", ""]
    if not ast.data_items:
        lines.append("No data items defined.")
        return "\n".join(lines)

    for item in ast.data_items:
        _format_data_item(item, lines, indent=0)
    lines.append("")
    return "\n".join(lines)


def _format_data_item(item, lines: list[str], indent: int) -> None:
    """Recursively format a data item and its children."""
    prefix = "  " * indent
    parts = [f"{prefix}{item.level:02d} {item.name}"]
    if item.pic:
        parts.append(f"PIC {item.pic}")
    if item.usage:
        parts.append(item.usage)
    if item.value is not None:
        parts.append(f"VALUE {item.value}")
    if item.occurs:
        parts.append(f"OCCURS {item.occurs}")
    if item.redefines:
        parts.append(f"REDEFINES {item.redefines}")
    if item.is_condition:
        vals = ", ".join(item.condition_values) if item.condition_values else "?"
        parts.append(f"VALUE {vals}")

    lines.append(" ".join(parts))
    for child in item.children:
        _format_data_item(child, lines, indent + 1)


def _build_paragraphs_section(ast: ASTOutput) -> str:
    """Build paragraphs section of the prompt."""
    lines = ["## Paragraphs", ""]
    if not ast.paragraphs:
        lines.append("No paragraphs defined.")
        return "\n".join(lines)

    for para in ast.paragraphs:
        lines.append(f"### {para.name}")
        for stmt in para.statements:
            lines.append(_format_statement(stmt, indent=0))
        lines.append("")

    return "\n".join(lines)


def _format_statement(stmt, indent: int = 0) -> str:
    """Format a statement node with children."""
    prefix = "  " * indent
    parts = [f"{prefix}- {stmt.type}"]
    if stmt.target:
        parts.append(f"-> {stmt.target}")
    if stmt.condition:
        parts.append(f"[{stmt.condition}]")

    result = " ".join(parts)
    for child in stmt.children:
        result += "\n" + _format_statement(child, indent + 1)
    return result


def _build_rules_section(rules: RulesOutput) -> str:
    """Build business rules section of the prompt."""
    lines = ["## Extracted Business Rules", ""]
    for rule in rules.rules:
        lines.append(f"- **{rule.rule_id}** ({rule.type}): `{rule.condition}`")
        if rule.paragraph:
            lines.append(f"  Paragraph: {rule.paragraph}")
        if rule.actions:
            lines.append(f"  Actions: {', '.join(rule.actions)}")
    lines.append("")
    return "\n".join(lines)


def _build_graph_section(graph: CallGraphOutput, program_id: str | None) -> str:
    """Build call graph section relevant to this program."""
    lines = ["## Call Graph Context", ""]

    outgoing = [e for e in graph.edges if e.caller == program_id]
    incoming = [e for e in graph.edges if e.callee == program_id]

    if outgoing:
        lines.append("Calls:")
        for edge in outgoing:
            ext = " (external)" if edge.callee in graph.external_calls else ""
            lines.append(f"  - {edge.callee}{ext}")

    if incoming:
        lines.append("Called by:")
        for edge in incoming:
            lines.append(f"  - {edge.caller}")

    if graph.entry_points and program_id in graph.entry_points:
        lines.append(f"{program_id} is an entry point (not called by other programs).")

    lines.append("")
    return "\n".join(lines)


def _truncate_to_budget(text: str, max_chars: int) -> str:
    """Truncate text to fit within character budget, preserving structure."""
    if len(text) <= max_chars:
        return text
    cutoff = max_chars - 200
    truncated = text[:cutoff]
    last_newline = truncated.rfind("\n")
    if last_newline > cutoff * 0.8:
        truncated = truncated[:last_newline]
    truncated += "\n\n[... truncated to fit context window ...]"
    return truncated


def _compose_prompt_with_budget(
    high_priority_sections: list[str],
    data_section: str,
    paragraph_section: str,
    max_context_chars: int,
) -> str:
    """Compose prompt while protecting high-value sections from tail truncation."""
    separator = "\n"
    high_priority_text = separator.join(high_priority_sections)
    if len(high_priority_text) >= max_context_chars:
        return _truncate_to_budget(high_priority_text, max_context_chars)

    remaining = max_context_chars - len(high_priority_text) - len(separator) * 2
    if remaining <= 0:
        return high_priority_text

    full_prompt = separator.join([high_priority_text, data_section, paragraph_section])
    if len(full_prompt) <= max_context_chars:
        return full_prompt

    data_budget = max(120, int(remaining * 0.35))
    paragraph_budget = max(200, remaining - data_budget)

    if data_budget + paragraph_budget > remaining:
        paragraph_budget = max(80, remaining - data_budget)
    if paragraph_budget < 80:
        paragraph_budget = 80
        data_budget = max(80, remaining - paragraph_budget)

    fitted_data = (
        data_section
        if len(data_section) <= data_budget
        else _truncate_to_budget(data_section, data_budget)
    )
    fitted_paragraphs = (
        paragraph_section
        if len(paragraph_section) <= paragraph_budget
        else _truncate_to_budget(paragraph_section, paragraph_budget)
    )

    composed = separator.join([high_priority_text, fitted_data, fitted_paragraphs])
    if len(composed) > max_context_chars:
        return _truncate_to_budget(composed, max_context_chars)
    return composed
