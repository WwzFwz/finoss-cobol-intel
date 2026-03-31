"""CALL graph builder — builds inter-program dependency graph from parse results."""

from __future__ import annotations

from cobol_intel.contracts.graph_output import CallEdge, CallGraphOutput
from cobol_intel.parsers.base import ParseResult, StatementNode


def build_call_graph(results: list[ParseResult]) -> CallGraphOutput:
    """Build a call graph from multiple parsed COBOL programs.

    Args:
        results: List of ParseResult from parsing multiple COBOL files.

    Returns:
        CallGraphOutput with nodes, edges, entry points, and external calls.
    """
    known_programs: set[str] = set()
    edges: list[CallEdge] = []
    all_callees: set[str] = set()

    for result in results:
        if result.success and result.program_id:
            known_programs.add(result.program_id)

    for result in results:
        if not result.success or not result.program_id:
            continue
        caller = result.program_id
        targets = _extract_call_targets(result)
        for callee, call_type in targets:
            edges.append(CallEdge(
                caller=caller,
                callee=callee,
                call_type=call_type,
            ))
            all_callees.add(callee)

    external = sorted(all_callees - known_programs)
    entry_points = sorted(known_programs - all_callees)
    nodes = sorted(known_programs | all_callees)
    adjacency = _build_adjacency(edges, known_programs)

    return CallGraphOutput(
        nodes=nodes,
        edges=edges,
        adjacency=adjacency,
        entry_points=entry_points,
        external_calls=external,
    )


def _extract_call_targets(result: ParseResult) -> list[tuple[str, str]]:
    """Extract (callee_name, call_type) pairs from all paragraphs."""
    targets: list[tuple[str, str]] = []
    for para in result.paragraphs:
        for stmt in para.statements:
            _collect_calls(stmt, targets)
    return targets


def _collect_calls(stmt: StatementNode, targets: list[tuple[str, str]]) -> None:
    """Recursively collect CALL targets from a statement tree."""
    if stmt.type == "CALL" and stmt.target:
        targets.append((stmt.target, "STATIC"))
    for child in stmt.children:
        _collect_calls(child, targets)


def _build_adjacency(edges: list[CallEdge], known_programs: set[str]) -> dict[str, list[str]]:
    """Build adjacency list for all known programs."""
    adjacency: dict[str, set[str]] = {program: set() for program in known_programs}
    for edge in edges:
        adjacency.setdefault(edge.caller, set()).add(edge.callee)

    return {
        caller: sorted(callees)
        for caller, callees in sorted(adjacency.items())
    }
