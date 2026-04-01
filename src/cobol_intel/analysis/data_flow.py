"""Data flow analyzer — builds field-level read/write flow graph.

Leverages the reference index for field classification and builds
directed edges between fields based on statement semantics.
"""

from __future__ import annotations

import re

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, StatementOut
from cobol_intel.contracts.data_flow_output import DataFlowEdge, DataFlowGraph, FlowType
from cobol_intel.contracts.reference_output import ReferenceIndex

_MOVE_PATTERN = re.compile(
    r"MOVE\s+(.+?)\s+TO\s+(.+)", re.IGNORECASE,
)
_COMPUTE_PATTERN = re.compile(
    r"COMPUTE\s+(\S+)\s*=\s*(.+)", re.IGNORECASE,
)
_READ_INTO_PATTERN = re.compile(
    r"READ\s+(\S+)\s+INTO\s+(\S+)", re.IGNORECASE,
)
_WRITE_FROM_PATTERN = re.compile(
    r"WRITE\s+(\S+)\s+FROM\s+(\S+)", re.IGNORECASE,
)
_REWRITE_FROM_PATTERN = re.compile(
    r"REWRITE\s+(\S+)\s+FROM\s+(\S+)", re.IGNORECASE,
)
_CALL_USING_PATTERN = re.compile(
    r"CALL\s+\S+\s+USING\s+(.+)", re.IGNORECASE,
)


def analyze_data_flow(
    ast: ASTOutput,
    reference_index: ReferenceIndex | None = None,
) -> DataFlowGraph:
    """Build a data flow graph from an AST."""
    program_id = ast.program_id or ""
    defined = _collect_defined_fields(ast.data_items)
    defined_upper = {f.upper() for f in defined}

    edges: list[DataFlowEdge] = []
    read_count: dict[str, int] = {}
    write_count: dict[str, int] = {}
    output_field_set: set[str] = set()

    for para in ast.paragraphs:
        for stmt in _flatten(para.statements):
            stmt_edges = _extract_edges(
                stmt, para.name, program_id, defined_upper,
            )
            edges.extend(stmt_edges)

            # Track output fields (written to file or passed to CALL)
            for edge in stmt_edges:
                if edge.flow_type in (
                    FlowType.WRITE_FROM,
                    FlowType.REWRITE_FROM,
                    FlowType.CALL_PARAM,
                ):
                    output_field_set.add(edge.source_field)

    # Use reference index for counts if available
    if reference_index:
        read_count = dict(reference_index.field_read_count)
        write_count = dict(reference_index.field_write_count)
    else:
        for edge in edges:
            if edge.source_field:
                read_count[edge.source_field] = (
                    read_count.get(edge.source_field, 0) + 1
                )
            if edge.target_field:
                write_count[edge.target_field] = (
                    write_count.get(edge.target_field, 0) + 1
                )

    entry_fields = list(ast.procedure_using)

    return DataFlowGraph(
        program_id=program_id,
        file_path=ast.file_path,
        edges=edges,
        field_read_count=read_count,
        field_write_count=write_count,
        entry_fields=entry_fields,
        output_fields=sorted(output_field_set),
    )


def _extract_edges(
    stmt: StatementOut,
    paragraph: str,
    program_id: str,
    defined_fields: set[str],
) -> list[DataFlowEdge]:
    """Extract data flow edges from a single statement."""
    edges: list[DataFlowEdge] = []
    raw_upper = (stmt.raw or "").upper().strip()

    if stmt.type == "MOVE":
        match = _MOVE_PATTERN.match(raw_upper)
        if match:
            sources = _extract_fields(match.group(1), defined_fields)
            targets = _extract_fields(match.group(2), defined_fields)
            for src in sources:
                for tgt in targets:
                    edges.append(DataFlowEdge(
                        source_field=src,
                        target_field=tgt,
                        flow_type=FlowType.MOVE,
                        paragraph=paragraph,
                        program_id=program_id,
                        statement_raw=stmt.raw,
                    ))

    elif stmt.type == "COMPUTE":
        match = _COMPUTE_PATTERN.match(raw_upper)
        if match:
            targets = _extract_fields(match.group(1), defined_fields)
            sources = _extract_fields(match.group(2), defined_fields)
            for src in sources:
                for tgt in targets:
                    edges.append(DataFlowEdge(
                        source_field=src,
                        target_field=tgt,
                        flow_type=FlowType.COMPUTE,
                        paragraph=paragraph,
                        program_id=program_id,
                        statement_raw=stmt.raw,
                    ))

    elif stmt.type == "READ":
        match = _READ_INTO_PATTERN.match(raw_upper)
        if match:
            file_name = match.group(1).strip()
            into_fields = _extract_fields(
                match.group(2), defined_fields,
            )
            for field in into_fields:
                edges.append(DataFlowEdge(
                    source_field=file_name,
                    target_field=field,
                    flow_type=FlowType.READ_INTO,
                    paragraph=paragraph,
                    program_id=program_id,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type == "WRITE":
        match = _WRITE_FROM_PATTERN.match(raw_upper)
        if match:
            record = match.group(1).strip()
            from_fields = _extract_fields(
                match.group(2), defined_fields,
            )
            for field in from_fields:
                edges.append(DataFlowEdge(
                    source_field=field,
                    target_field=record,
                    flow_type=FlowType.WRITE_FROM,
                    paragraph=paragraph,
                    program_id=program_id,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type == "REWRITE":
        match = _REWRITE_FROM_PATTERN.match(raw_upper)
        if match:
            record = match.group(1).strip()
            from_fields = _extract_fields(
                match.group(2), defined_fields,
            )
            for field in from_fields:
                edges.append(DataFlowEdge(
                    source_field=field,
                    target_field=record,
                    flow_type=FlowType.REWRITE_FROM,
                    paragraph=paragraph,
                    program_id=program_id,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type == "CALL":
        match = _CALL_USING_PATTERN.match(raw_upper)
        if match:
            params = _extract_fields(
                match.group(1), defined_fields,
            )
            target = stmt.target or "UNKNOWN"
            for field in params:
                edges.append(DataFlowEdge(
                    source_field=field,
                    target_field=target,
                    flow_type=FlowType.CALL_PARAM,
                    paragraph=paragraph,
                    program_id=program_id,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type in ("IF", "EVALUATE"):
        condition = (stmt.condition or "").upper()
        if condition:
            fields = _extract_fields(condition, defined_fields)
            for field in fields:
                edges.append(DataFlowEdge(
                    source_field=field,
                    target_field="",
                    flow_type=FlowType.CONDITION_READ,
                    paragraph=paragraph,
                    program_id=program_id,
                    statement_raw=stmt.raw,
                ))

    return edges


def _extract_fields(
    text: str, defined_fields: set[str],
) -> list[str]:
    """Extract known field names from text."""
    tokens = re.split(r"[\s,()=+*/><]+", text)
    found: list[str] = []
    for token in tokens:
        cleaned = token.strip().rstrip(".")
        if cleaned and cleaned in defined_fields:
            found.append(cleaned)
    return found


def _collect_defined_fields(
    items: list[DataItemOut],
) -> list[str]:
    """Recursively collect all data item names."""
    result: list[str] = []
    for item in items:
        result.append(item.name)
        result.extend(_collect_defined_fields(item.children))
    return result


def _flatten(
    statements: list[StatementOut],
) -> list[StatementOut]:
    """Flatten nested statements."""
    result: list[StatementOut] = []
    for stmt in statements:
        result.append(stmt)
        result.extend(_flatten(stmt.children))
    return result
