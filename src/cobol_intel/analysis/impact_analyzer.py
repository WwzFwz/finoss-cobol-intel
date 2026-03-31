"""Change impact analyzer using call graph traversal and field reference scanning."""

from __future__ import annotations

from collections import deque

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.impact_output import ImpactedEntity, ImpactReport, ImpactType
from cobol_intel.contracts.rules_output import RulesOutput


def analyze_impact(
    changed_programs: list[str],
    changed_fields: list[str],
    call_graph: CallGraphOutput,
    rules_by_program: dict[str, RulesOutput] | None = None,
    asts_by_program: dict[str, ASTOutput] | None = None,
    max_depth: int = 3,
) -> ImpactReport:
    """Compute change impact using call graph traversal and field reference matching.

    Algorithm:
    1. For each changed program, BFS through reverse adjacency to find callers.
    2. For each changed field, scan all ASTs + rules for references.
    3. Merge and deduplicate.
    """
    rules_by_program = rules_by_program or {}
    asts_by_program = asts_by_program or {}
    impacted: dict[str, ImpactedEntity] = {}

    # 1. Call graph impact (reverse traversal)
    reverse_adj = _reverse_adjacency(call_graph.adjacency)
    for changed_prog in changed_programs:
        callers = _bfs_callers(changed_prog, reverse_adj, max_depth)
        for caller_id, distance in callers.items():
            if caller_id in changed_programs:
                continue
            impact_type = ImpactType.DIRECT_CALLER if distance == 1 else ImpactType.TRANSITIVE_CALLER
            entity = impacted.get(caller_id, ImpactedEntity(
                program_id=caller_id,
                file_path=asts_by_program[caller_id].file_path if caller_id in asts_by_program else "",
                impact_type=impact_type,
                distance=distance,
                reason=f"Calls {changed_prog}" if distance == 1 else f"Transitive caller of {changed_prog} (depth {distance})",
            ))
            if caller_id not in impacted or distance < impacted[caller_id].distance:
                impacted[caller_id] = entity

    # 2. Field reference impact
    for field_name in changed_fields:
        field_upper = field_name.upper()
        for prog_id, ast in asts_by_program.items():
            if prog_id in changed_programs:
                continue
            paragraphs, rule_ids = _find_field_references(
                field_upper, ast, rules_by_program.get(prog_id),
            )
            if paragraphs or rule_ids:
                existing = impacted.get(prog_id)
                if existing:
                    existing.affected_paragraphs = sorted(set(existing.affected_paragraphs) | set(paragraphs))
                    existing.affected_rules = sorted(set(existing.affected_rules) | set(rule_ids))
                else:
                    impacted[prog_id] = ImpactedEntity(
                        program_id=prog_id,
                        file_path=ast.file_path,
                        impact_type=ImpactType.FIELD_REFERENCE,
                        distance=0,
                        affected_paragraphs=paragraphs,
                        affected_rules=rule_ids,
                        reason=f"References field {field_name}",
                    )

    entities = sorted(impacted.values(), key=lambda e: (e.distance, e.program_id))
    return ImpactReport(
        changed_programs=changed_programs,
        changed_fields=changed_fields,
        impacted_entities=entities,
        total_impacted=len(entities),
    )


def _reverse_adjacency(adjacency: dict[str, list[str]]) -> dict[str, list[str]]:
    """Build reverse adjacency: callee -> list of callers."""
    reverse: dict[str, set[str]] = {}
    for caller, callees in adjacency.items():
        for callee in callees:
            reverse.setdefault(callee, set()).add(caller)
    return {k: sorted(v) for k, v in reverse.items()}


def _bfs_callers(
    start: str,
    reverse_adj: dict[str, list[str]],
    max_depth: int,
) -> dict[str, int]:
    """BFS from start through reverse adjacency, returning {program: distance}."""
    visited: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([(start, 0)])

    while queue:
        current, depth = queue.popleft()
        if depth > max_depth:
            continue
        for caller in reverse_adj.get(current, []):
            if caller not in visited:
                visited[caller] = depth + 1
                if depth + 1 < max_depth:
                    queue.append((caller, depth + 1))

    return visited


def _find_field_references(
    field_name: str,
    ast: ASTOutput,
    rules: RulesOutput | None,
) -> tuple[list[str], list[str]]:
    """Find paragraphs and rule IDs that reference a field name."""
    paragraphs: set[str] = set()
    rule_ids: set[str] = set()

    # Scan data items
    for item in ast.data_items:
        if _data_item_matches(item, field_name):
            # Field is defined in this program
            for para in ast.paragraphs:
                for stmt in para.statements:
                    if _statement_references(stmt, field_name):
                        paragraphs.add(para.name)

    # Scan paragraphs for statement references
    for para in ast.paragraphs:
        for stmt in para.statements:
            if _statement_references(stmt, field_name):
                paragraphs.add(para.name)

    # Scan rules
    if rules:
        for rule in rules.rules:
            if field_name in (rule.condition or "").upper():
                rule_ids.add(rule.rule_id)
                if rule.paragraph:
                    paragraphs.add(rule.paragraph)

    return sorted(paragraphs), sorted(rule_ids)


def _data_item_matches(item: DataItemOut, field_name: str) -> bool:
    if item.name.upper() == field_name:
        return True
    return any(_data_item_matches(child, field_name) for child in item.children)


def _statement_references(stmt, field_name: str) -> bool:
    """Check if a statement references a field name in target, condition, or raw."""
    for text in (stmt.target, stmt.condition, stmt.raw):
        if text and field_name in text.upper():
            return True
    return any(_statement_references(child, field_name) for child in stmt.children)
