"""Field reference indexer — classifies field reads, writes, and conditions.

Walks the AST and builds a per-program index of how each data item is used:
- READ: field appears as source in MOVE/COMPUTE, or in condition
- WRITE: field appears as target in MOVE/COMPUTE/READ INTO
- CONDITION: field appears in IF/EVALUATE condition
- CALL_PARAM: field appears in CALL ... USING
"""

from __future__ import annotations

import re

from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, StatementOut
from cobol_intel.contracts.reference_output import (
    FieldReference,
    ReferenceIndex,
    ReferenceType,
)

# Patterns for parsing COBOL statement text
_MOVE_PATTERN = re.compile(
    r"MOVE\s+(.+?)\s+TO\s+(.+)", re.IGNORECASE,
)
_COMPUTE_PATTERN = re.compile(
    r"COMPUTE\s+(\S+)\s*=\s*(.+)", re.IGNORECASE,
)
_READ_INTO_PATTERN = re.compile(
    r"READ\s+\S+\s+INTO\s+(\S+)", re.IGNORECASE,
)
_WRITE_FROM_PATTERN = re.compile(
    r"WRITE\s+\S+\s+FROM\s+(\S+)", re.IGNORECASE,
)
_REWRITE_FROM_PATTERN = re.compile(
    r"REWRITE\s+\S+\s+FROM\s+(\S+)", re.IGNORECASE,
)
_CALL_USING_PATTERN = re.compile(
    r"CALL\s+\S+\s+USING\s+(.+)", re.IGNORECASE,
)


def build_reference_index(ast: ASTOutput) -> ReferenceIndex:
    """Build a field reference index from an AST."""
    defined = _collect_defined_fields(ast.data_items)
    defined_upper = {f.upper() for f in defined}
    references: list[FieldReference] = []
    unsupported: set[str] = set()

    for para in ast.paragraphs:
        for stmt in _flatten(para.statements):
            refs, stmt_unsupported = _classify_statement(
                stmt, para.name, defined_upper,
            )
            references.extend(refs)
            unsupported.update(stmt_unsupported)

    # Build read/write counts
    read_count: dict[str, int] = {}
    write_count: dict[str, int] = {}
    for ref in references:
        if ref.reference_type in (
            ReferenceType.READ, ReferenceType.CONDITION,
            ReferenceType.CALL_PARAM,
        ):
            read_count[ref.field_name] = (
                read_count.get(ref.field_name, 0) + 1
            )
        if ref.reference_type == ReferenceType.WRITE:
            write_count[ref.field_name] = (
                write_count.get(ref.field_name, 0) + 1
            )

    return ReferenceIndex(
        program_id=ast.program_id or "",
        file_path=ast.file_path,
        references=references,
        field_read_count=read_count,
        field_write_count=write_count,
        defined_fields=sorted(defined),
        entry_fields=list(ast.procedure_using),
        unsupported_constructs=sorted(unsupported),
    )


def _collect_defined_fields(
    items: list[DataItemOut],
) -> list[str]:
    """Recursively collect all data item names."""
    result: list[str] = []
    for item in items:
        result.append(item.name)
        result.extend(_collect_defined_fields(item.children))
    return result


def _classify_statement(
    stmt: StatementOut,
    paragraph: str,
    defined_fields: set[str],
) -> tuple[list[FieldReference], set[str]]:
    """Classify field references in a single statement."""
    refs: list[FieldReference] = []
    unsupported: set[str] = set()
    raw_upper = (stmt.raw or "").upper().strip()

    if stmt.type == "MOVE":
        match = _MOVE_PATTERN.match(raw_upper)
        if match:
            source = match.group(1).strip()
            targets_str = match.group(2).strip()
            # Source is read
            for field in _extract_field_names(source, defined_fields):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.READ,
                    paragraph=paragraph,
                    statement_type="MOVE",
                    statement_raw=stmt.raw,
                ))
            # Targets are written
            for target in _split_targets(targets_str):
                for field in _extract_field_names(target, defined_fields):
                    refs.append(FieldReference(
                        field_name=field,
                        reference_type=ReferenceType.WRITE,
                        paragraph=paragraph,
                        statement_type="MOVE",
                        statement_raw=stmt.raw,
                    ))

    elif stmt.type == "COMPUTE":
        match = _COMPUTE_PATTERN.match(raw_upper)
        if match:
            target = match.group(1).strip()
            expr = match.group(2).strip()
            for field in _extract_field_names(target, defined_fields):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.WRITE,
                    paragraph=paragraph,
                    statement_type="COMPUTE",
                    statement_raw=stmt.raw,
                ))
            for field in _extract_field_names(expr, defined_fields):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.READ,
                    paragraph=paragraph,
                    statement_type="COMPUTE",
                    statement_raw=stmt.raw,
                ))

    elif stmt.type in ("ADD", "SUBTRACT", "MULTIPLY"):
        # These read operands and write to target (after TO/GIVING)
        for field in _extract_field_names(raw_upper, defined_fields):
            refs.append(FieldReference(
                field_name=field,
                reference_type=ReferenceType.READ,
                paragraph=paragraph,
                statement_type=stmt.type,
                statement_raw=stmt.raw,
            ))

    elif stmt.type == "READ":
        match = _READ_INTO_PATTERN.match(raw_upper)
        if match:
            into_field = match.group(1).strip()
            for field in _extract_field_names(
                into_field, defined_fields,
            ):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.WRITE,
                    paragraph=paragraph,
                    statement_type="READ",
                    statement_raw=stmt.raw,
                ))

    elif stmt.type in ("WRITE", "REWRITE"):
        pattern = (
            _WRITE_FROM_PATTERN if stmt.type == "WRITE"
            else _REWRITE_FROM_PATTERN
        )
        match = pattern.match(raw_upper)
        if match:
            from_field = match.group(1).strip()
            for field in _extract_field_names(
                from_field, defined_fields,
            ):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.READ,
                    paragraph=paragraph,
                    statement_type=stmt.type,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type == "CALL":
        match = _CALL_USING_PATTERN.match(raw_upper)
        if match:
            params_str = match.group(1).strip()
            for token in params_str.split():
                for field in _extract_field_names(
                    token, defined_fields,
                ):
                    refs.append(FieldReference(
                        field_name=field,
                        reference_type=ReferenceType.CALL_PARAM,
                        paragraph=paragraph,
                        statement_type="CALL",
                        statement_raw=stmt.raw,
                    ))

    elif stmt.type in ("IF", "EVALUATE"):
        condition = (stmt.condition or "").upper()
        if condition:
            for field in _extract_field_names(
                condition, defined_fields,
            ):
                refs.append(FieldReference(
                    field_name=field,
                    reference_type=ReferenceType.CONDITION,
                    paragraph=paragraph,
                    statement_type=stmt.type,
                    statement_raw=stmt.raw,
                ))

    elif stmt.type == "DISPLAY":
        for field in _extract_field_names(raw_upper, defined_fields):
            refs.append(FieldReference(
                field_name=field,
                reference_type=ReferenceType.READ,
                paragraph=paragraph,
                statement_type="DISPLAY",
                statement_raw=stmt.raw,
            ))

    # Track unsupported constructs
    if stmt.type in ("GO-TO", "ALTER"):
        label = stmt.type.replace("-", " ")
        unsupported.add(label)

    return refs, unsupported


def _extract_field_names(
    text: str, defined_fields: set[str],
) -> list[str]:
    """Extract known field names from a text fragment."""
    # Split on whitespace and arithmetic/comparison operators but NOT hyphens
    # (COBOL field names like WS-BALANCE contain hyphens)
    tokens = re.split(r"[\s,()=+*/><]+", text)
    found: list[str] = []
    for token in tokens:
        cleaned = token.strip().rstrip(".")
        if cleaned and cleaned in defined_fields:
            found.append(cleaned)
    return found


def _split_targets(text: str) -> list[str]:
    """Split MOVE target list (e.g., 'A B C' or 'A, B')."""
    return [t.strip().rstrip(".") for t in re.split(r"[\s,]+", text) if t.strip()]


def _flatten(
    statements: list[StatementOut],
) -> list[StatementOut]:
    """Flatten nested statements into a flat list."""
    result: list[StatementOut] = []
    for stmt in statements:
        result.append(stmt)
        result.extend(_flatten(stmt.children))
    return result
