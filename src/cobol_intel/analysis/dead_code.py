"""Dead code detector — unreachable paragraphs, unused data items, dead branches.

Uses CFG paragraph reachability and reference index for accuracy.
Conservative by design: only flags dead code with sufficient evidence.
"""

from __future__ import annotations

import re
from collections import deque

from cobol_intel.analysis.cfg_builder import _expand_perform_targets
from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, StatementOut
from cobol_intel.contracts.cfg_output import ControlFlowGraph
from cobol_intel.contracts.dead_code_output import (
    Confidence,
    DeadCodeItem,
    DeadCodeReport,
    DeadCodeType,
)
from cobol_intel.contracts.reference_output import ReferenceIndex


def detect_dead_code(
    ast: ASTOutput,
    cfg: ControlFlowGraph | None = None,
    reference_index: ReferenceIndex | None = None,
) -> DeadCodeReport:
    """Detect dead code in a COBOL program.

    Uses CFG for paragraph reachability and reference index for field usage.
    Falls back to statement-level scanning when CFG/ref index are absent.
    """
    items: list[DeadCodeItem] = []
    warnings: list[str] = []
    program_id = ast.program_id or ""
    file_path = ast.file_path

    has_unsupported = bool(
        cfg and cfg.unsupported_constructs
    ) or bool(
        reference_index and reference_index.unsupported_constructs
    )

    if has_unsupported:
        constructs = set()
        if cfg:
            constructs.update(cfg.unsupported_constructs)
        if reference_index:
            constructs.update(reference_index.unsupported_constructs)
        warnings.append(
            "Program uses "
            + ", ".join(sorted(constructs))
            + " — results may be incomplete"
        )

    # 1. Unreachable paragraphs
    unreachable = _find_unreachable_paragraphs(ast, cfg)
    confidence = Confidence.MEDIUM if has_unsupported else Confidence.HIGH
    for para_name in unreachable:
        items.append(DeadCodeItem(
            type=DeadCodeType.UNREACHABLE_PARAGRAPH,
            name=para_name,
            file_path=file_path,
            program_id=program_id,
            reason="No PERFORM or fallthrough reaches this paragraph",
            confidence=confidence,
        ))

    # 2. Unused data items
    unused = _find_unused_data_items(ast, reference_index)
    for field_name in unused:
        items.append(DeadCodeItem(
            type=DeadCodeType.UNUSED_DATA_ITEM,
            name=field_name,
            file_path=file_path,
            program_id=program_id,
            reason="Field is defined but never referenced in any statement",
            confidence=Confidence.HIGH,
        ))

    # 3. Dead branches
    dead_branches = _find_dead_branches(ast)
    for name, reason in dead_branches:
        items.append(DeadCodeItem(
            type=DeadCodeType.DEAD_BRANCH,
            name=name,
            file_path=file_path,
            program_id=program_id,
            reason=reason,
            confidence=Confidence.HIGH,
        ))

    total_dead = len(items)
    total_paragraphs = len(ast.paragraphs)
    pct = (
        (len(unreachable) / total_paragraphs * 100.0)
        if total_paragraphs > 0 else 0.0
    )

    return DeadCodeReport(
        program_id=program_id,
        file_path=file_path,
        items=items,
        total_dead=total_dead,
        dead_code_percentage=round(pct, 1),
        warnings=warnings,
    )


def _find_unreachable_paragraphs(
    ast: ASTOutput,
    cfg: ControlFlowGraph | None,
) -> list[str]:
    """Find paragraphs not reachable from the entry point."""
    if not ast.paragraphs:
        return []

    all_paras = [p.name for p in ast.paragraphs]
    if len(all_paras) <= 1:
        return []

    # Build reachability via CFG perform_targets + fallthrough
    if cfg and cfg.perform_targets:
        reachable = _reachable_from_cfg(ast, cfg)
    else:
        reachable = _reachable_from_statements(ast)

    return [p for p in all_paras if p not in reachable]


def _reachable_from_cfg(
    ast: ASTOutput,
    cfg: ControlFlowGraph,
) -> set[str]:
    """BFS reachability using CFG perform targets and fallthrough edges.

    Key COBOL semantics: PERFORM'd paragraphs return to caller, so they
    do NOT fall through to the next paragraph. Only paragraphs reached
    via sequential execution (fallthrough) can fall through further.
    """
    all_paras = [p.name for p in ast.paragraphs]
    if not all_paras:
        return set()

    exit_paras: set[str] = set()
    for block_id in cfg.exit_blocks:
        para = block_id.rsplit(":", 1)[0]
        exit_paras.add(para)

    # Collect all PERFORM targets (these don't fall through)
    perform_target_set: set[str] = set()
    for targets in cfg.perform_targets.values():
        perform_target_set.update(targets)

    para_index = {name: i for i, name in enumerate(all_paras)}

    # BFS with flow type tracking: (paragraph, is_sequential)
    visited: set[str] = set()
    queue: deque[tuple[str, bool]] = deque([(all_paras[0], True)])
    visited.add(all_paras[0])

    while queue:
        current, is_sequential = queue.popleft()

        # Add PERFORM targets as reachable (but not sequential)
        for target in cfg.perform_targets.get(current, []):
            if target not in visited:
                visited.add(target)
                queue.append((target, False))

        # Add fallthrough to next paragraph ONLY if:
        # 1. This paragraph was reached sequentially (not via PERFORM)
        # 2. This paragraph doesn't end with an exit statement
        if is_sequential and current not in exit_paras:
            idx = para_index.get(current, -1)
            if 0 <= idx < len(all_paras) - 1:
                nxt = all_paras[idx + 1]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, True))

    return visited


def _reachable_from_statements(ast: ASTOutput) -> set[str]:
    """Fallback: build reachability from PERFORM targets in statements."""
    all_paras = [p.name for p in ast.paragraphs]
    if not all_paras:
        return set()

    perform_targets_map: dict[str, list[str]] = {}
    exit_paras: set[str] = set()
    paragraph_names = [paragraph.name for paragraph in ast.paragraphs]

    for para in ast.paragraphs:
        targets: list[str] = []
        for stmt in _flatten(para.statements):
            targets.extend(_expand_perform_targets(stmt, paragraph_names))
            if stmt.type in ("STOP-RUN", "GOBACK"):
                exit_paras.add(para.name)
        if targets:
            perform_targets_map[para.name] = targets

    para_index = {name: i for i, name in enumerate(all_paras)}

    # BFS with flow type tracking
    visited: set[str] = set()
    queue: deque[tuple[str, bool]] = deque([(all_paras[0], True)])
    visited.add(all_paras[0])

    while queue:
        current, is_sequential = queue.popleft()

        for target in perform_targets_map.get(current, []):
            if target not in visited:
                visited.add(target)
                queue.append((target, False))

        if is_sequential and current not in exit_paras:
            idx = para_index.get(current, -1)
            if 0 <= idx < len(all_paras) - 1:
                nxt = all_paras[idx + 1]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, True))

    return visited


def _find_unused_data_items(
    ast: ASTOutput,
    reference_index: ReferenceIndex | None,
) -> list[str]:
    """Find data items that are defined but never referenced."""
    if not ast.data_items:
        return []

    if reference_index:
        referenced = {r.field_name for r in reference_index.references}
        # Also count entry fields as used
        referenced.update(
            f.upper() for f in reference_index.entry_fields
        )
    else:
        # Fallback: scan raw statements for field mentions
        referenced = _scan_all_field_mentions(ast)

    unused: list[str] = []
    _check_unused_items(ast.data_items, referenced, unused)
    return unused


def _check_unused_items(
    items: list[DataItemOut],
    referenced: set[str],
    unused: list[str],
) -> bool:
    """Check items for unused fields. Returns True if any child is used."""
    for item in items:
        name_upper = item.name.upper()
        children_used = _check_unused_items(
            item.children, referenced, unused,
        )
        # Skip FILLER and level-88 conditions (they're used implicitly)
        if name_upper == "FILLER" or item.is_condition:
            continue
        # If a group item has used children, the group is used
        if children_used:
            continue
        if name_upper not in referenced:
            unused.append(item.name)
    # Return whether any item in this list is used
    return any(
        item.name.upper() in referenced
        or item.is_condition
        or item.name.upper() == "FILLER"
        for item in items
    )


def _scan_all_field_mentions(ast: ASTOutput) -> set[str]:
    """Fallback: scan all statements for field name mentions."""
    mentioned: set[str] = set()
    for para in ast.paragraphs:
        for stmt in _flatten(para.statements):
            for text in (stmt.target, stmt.condition, stmt.raw):
                if text:
                    for token in text.upper().split():
                        mentioned.add(token.rstrip("."))
    # Also add procedure_using as used
    mentioned.update(f.upper() for f in ast.procedure_using)
    return mentioned


def _find_dead_branches(
    ast: ASTOutput,
) -> list[tuple[str, str]]:
    """Find trivially dead branches (constant conditions)."""
    results: list[tuple[str, str]] = []
    for para in ast.paragraphs:
        for stmt in _flatten(para.statements):
            if stmt.type in ("IF", "EVALUATE") and stmt.condition:
                dead = _is_trivially_dead_condition(stmt.condition)
                if dead:
                    name = f"{para.name}:{stmt.type}"
                    results.append((name, dead))
    return results


# Patterns for trivially constant conditions
_ALWAYS_TRUE = re.compile(
    r"^(\S+)\s*=\s*\1$", re.IGNORECASE,
)
_LITERAL_TRUE = re.compile(
    r"^(\d+)\s*=\s*\1$",
)


def _is_trivially_dead_condition(condition: str) -> str | None:
    """Check if a condition is trivially always true or always false.

    Returns a reason string if dead, None otherwise.
    Conservative: only flags obvious cases.
    """
    cond = condition.strip()

    # "X = X" (same variable compared to itself)
    if _ALWAYS_TRUE.match(cond):
        return f"Condition '{cond}' is always true (same operand on both sides)"

    # "1 = 1", "0 = 0" etc.
    if _LITERAL_TRUE.match(cond):
        return f"Condition '{cond}' is always true (literal comparison)"

    return None


def _flatten(
    statements: list[StatementOut],
) -> list[StatementOut]:
    """Flatten nested statements."""
    result: list[StatementOut] = []
    for stmt in statements:
        result.append(stmt)
        result.extend(_flatten(stmt.children))
    return result
