"""Per-program documentation generator and project report builder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut
from cobol_intel.contracts.explanation_output import ExplanationOutput
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.manifest import Manifest
from cobol_intel.contracts.rules_output import RulesOutput


@dataclass
class ProgramDocumentation:
    program_id: str
    file_path: str
    markdown: str


def generate_program_doc(
    ast: ASTOutput,
    rules: RulesOutput | None = None,
    call_graph: CallGraphOutput | None = None,
    explanation: ExplanationOutput | None = None,
) -> ProgramDocumentation:
    """Generate comprehensive Markdown documentation for one COBOL program."""
    program_id = ast.program_id or Path(ast.file_path).stem or "UNKNOWN"
    lines: list[str] = []

    # Program header
    lines.extend([
        f"# {program_id}",
        "",
        f"- **File**: `{ast.file_path}`",
        f"- **Parser**: {ast.parser_name}",
    ])
    if ast.procedure_using:
        lines.append(f"- **PROCEDURE DIVISION USING**: {', '.join(ast.procedure_using)}")
    if ast.copybooks_used:
        lines.append(f"- **Copybooks**: {', '.join(ast.copybooks_used)}")
    lines.append("")

    # LLM summary (if available)
    if explanation and explanation.program_summary:
        lines.extend(["## Summary", "", explanation.program_summary, ""])

    # Data dictionary
    lines.extend(["## Data Dictionary", ""])
    if ast.data_items:
        lines.append("| Level | Name | PIC | Usage | Value | Occurs | Redefines |")
        lines.append("|-------|------|-----|-------|-------|--------|-----------|")
        for item in ast.data_items:
            _flatten_data_items(item, lines)
    else:
        lines.append("No data items defined.")
    lines.append("")

    # Procedure flow
    lines.extend(["## Procedure Flow", ""])
    if ast.paragraphs:
        for para in ast.paragraphs:
            stmt_types = sorted({s.type for s in para.statements})
            lines.append(f"- **{para.name}**: {', '.join(stmt_types) if stmt_types else 'empty'}")
    else:
        lines.append("No paragraphs defined.")
    lines.append("")

    # Business rules
    if rules and rules.rules:
        lines.extend(["## Business Rules", ""])
        lines.append("| Rule ID | Type | Condition | Paragraph | Actions |")
        lines.append("|---------|------|-----------|-----------|---------|")
        for rule in rules.rules:
            actions = ", ".join(rule.actions) if rule.actions else "-"
            para = rule.paragraph or "-"
            lines.append(f"| {rule.rule_id} | {rule.type} | `{rule.condition}` | {para} | {actions} |")
        lines.append("")

    # Call dependencies
    if call_graph and call_graph.edges:
        outgoing = [e for e in call_graph.edges if e.caller == program_id]
        incoming = [e for e in call_graph.edges if e.callee == program_id]
        if outgoing or incoming:
            lines.extend(["## Call Dependencies", ""])
            if outgoing:
                lines.append("**Calls:**")
                for edge in outgoing:
                    ext = " (external)" if edge.callee in call_graph.external_calls else ""
                    lines.append(f"- `{edge.callee}`{ext}")
                lines.append("")
            if incoming:
                lines.append("**Called by:**")
                for edge in incoming:
                    lines.append(f"- `{edge.caller}`")
                lines.append("")

    # LLM paragraph explanations
    if explanation and explanation.paragraph_explanations:
        lines.extend(["## Paragraph Details", ""])
        for pe in explanation.paragraph_explanations:
            lines.extend([f"### {pe.paragraph}", "", pe.summary, ""])

    return ProgramDocumentation(
        program_id=program_id,
        file_path=ast.file_path,
        markdown="\n".join(lines),
    )


def generate_project_report(
    manifest: Manifest,
    program_docs: list[ProgramDocumentation],
    call_graph: CallGraphOutput | None = None,
) -> str:
    """Generate consolidated Markdown report for entire project."""
    lines: list[str] = [
        f"# Project Report: {manifest.project_name}",
        "",
        f"- **Run ID**: `{manifest.run_id}`",
        f"- **Status**: `{manifest.status.value}`",
        f"- **Programs**: {len(program_docs)}",
        f"- **Warnings**: {len(manifest.warnings)}",
        f"- **Errors**: {len(manifest.errors)}",
    ]
    if manifest.governance.approved_backend:
        lines.append(f"- **Backend**: {manifest.governance.approved_backend}")
    if manifest.governance.token_usage.total_tokens:
        lines.append(f"- **Tokens used**: {manifest.governance.token_usage.total_tokens}")
    lines.append("")

    # Program inventory
    lines.extend(["## Program Inventory", ""])
    lines.append("| Program | File |")
    lines.append("|---------|------|")
    for doc in program_docs:
        lines.append(f"| {doc.program_id} | `{doc.file_path}` |")
    lines.append("")

    # Call graph
    if call_graph and call_graph.edges:
        lines.extend([
            "## Call Graph",
            "",
            "```mermaid",
            call_graph.to_mermaid(),
            "```",
            "",
        ])

    # Per-program sections
    for doc in program_docs:
        lines.extend(["---", "", doc.markdown])

    return "\n".join(lines)


def _flatten_data_items(item: DataItemOut, lines: list[str]) -> None:
    """Add data item as a table row, then recurse into children."""
    pic = item.pic or "-"
    usage = item.usage or "-"
    value = str(item.value) if item.value is not None else "-"
    occurs = str(item.occurs) if item.occurs else "-"
    redefines = item.redefines or "-"
    lines.append(f"| {item.level:02d} | {item.name} | {pic} | {usage} | {value} | {occurs} | {redefines} |")
    for child in item.children:
        _flatten_data_items(child, lines)
