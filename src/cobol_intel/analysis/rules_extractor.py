"""Business rules extractor — extracts IF/EVALUATE conditions from parse results."""

from __future__ import annotations

from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.contracts.source_ref import SourceRef
from cobol_intel.parsers.base import ParseResult, StatementNode


def extract_rules(result: ParseResult, file_path: str = "") -> RulesOutput:
    """Extract business rules from a parsed COBOL program.

    Walks all paragraphs and extracts IF and EVALUATE conditions
    as structured business rules.
    """
    rules: list[BusinessRule] = []
    counter = 0

    for para in result.paragraphs:
        for stmt in para.statements:
            counter = _collect_rules(
                stmt, para.name, file_path, rules, counter,
            )

    # Also extract 88-level condition names as business rules
    for item in _flatten_data_items(result.data_items):
        if item.is_condition and item.condition_values:
            counter += 1
            rules.append(BusinessRule(
                rule_id=f"R{counter:03d}",
                type="CONDITION-88",
                condition=f"{item.name} = {', '.join(item.condition_values)}",
                source=SourceRef(file=file_path) if file_path else None,
            ))

    return RulesOutput(
        program_id=result.program_id,
        file_path=file_path,
        rules=rules,
    )


def _collect_rules(
    stmt: StatementNode,
    paragraph: str,
    file_path: str,
    rules: list[BusinessRule],
    counter: int,
) -> int:
    """Recursively collect rules from a statement tree."""
    if stmt.type == "IF" and stmt.condition:
        counter += 1
        actions = [c.type for c in stmt.children]
        rules.append(BusinessRule(
            rule_id=f"R{counter:03d}",
            type="IF",
            condition=stmt.condition,
            actions=actions,
            paragraph=paragraph,
            source=SourceRef(file=file_path, paragraph=paragraph) if file_path else None,
        ))

    elif stmt.type == "EVALUATE" and stmt.condition:
        counter += 1
        actions = [c.type for c in stmt.children]
        rules.append(BusinessRule(
            rule_id=f"R{counter:03d}",
            type="EVALUATE",
            condition=f"EVALUATE {stmt.condition}",
            actions=actions,
            paragraph=paragraph,
            source=SourceRef(file=file_path, paragraph=paragraph) if file_path else None,
        ))

    # Recurse into children for nested rules
    for child in stmt.children:
        counter = _collect_rules(child, paragraph, file_path, rules, counter)

    return counter


def _flatten_data_items(items):
    """Flatten nested data items for scanning 88-level conditions."""
    result = []
    stack = list(items)
    while stack:
        item = stack.pop(0)
        result.append(item)
        stack.extend(item.children)
    return result
