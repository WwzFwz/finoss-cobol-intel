"""Intra-program control flow graph builder.

Builds a CFG from the AST by:
1. Creating blocks per paragraph (splitting at branch points).
2. Connecting blocks with sequential, branch, and perform edges.
3. Recording unsupported constructs (GO TO, ALTER, PERFORM THRU) as warnings.
"""

from __future__ import annotations

from cobol_intel.contracts.ast_output import ASTOutput, StatementOut
from cobol_intel.contracts.cfg_output import CFGBlock, CFGEdge, ControlFlowGraph

_BRANCH_TYPES = {"IF", "EVALUATE"}
_EXIT_TYPES = {"STOP-RUN", "GOBACK"}
_UNSUPPORTED_TYPES = {"GO-TO", "ALTER"}


def build_cfg(ast: ASTOutput) -> ControlFlowGraph:
    """Build an intra-program control flow graph from an AST."""
    blocks: list[CFGBlock] = []
    edges: list[CFGEdge] = []
    exit_blocks: list[str] = []
    perform_targets: dict[str, list[str]] = {}
    unsupported: set[str] = set()

    paragraph_block_ids: dict[str, str] = {}

    for para in ast.paragraphs:
        para_blocks, para_edges, para_unsupported = _build_paragraph_blocks(
            para.name, para.statements,
        )
        blocks.extend(para_blocks)
        edges.extend(para_edges)
        unsupported.update(para_unsupported)

        if para_blocks:
            paragraph_block_ids[para.name] = para_blocks[0].block_id

        # Collect perform targets and exit blocks from this paragraph
        targets: list[str] = []
        for stmt in _flatten_statements(para.statements):
            if stmt.type in ("PERFORM", "PERFORM-VARYING") and stmt.target:
                targets.append(stmt.target)
            if stmt.type in _EXIT_TYPES:
                for blk in para_blocks:
                    if stmt.type in blk.statement_types:
                        if blk.block_id not in exit_blocks:
                            exit_blocks.append(blk.block_id)
            if stmt.type in _UNSUPPORTED_TYPES:
                label = stmt.type.replace("-", " ")
                unsupported.add(label)

        if targets:
            perform_targets[para.name] = targets

    # Add perform edges: from paragraph containing PERFORM to target paragraph
    for para_name, targets in perform_targets.items():
        for target in targets:
            if target in paragraph_block_ids:
                source_block = paragraph_block_ids[para_name]
                target_block = paragraph_block_ids[target]
                edges.append(CFGEdge(
                    from_block=source_block,
                    to_block=target_block,
                    edge_type="perform",
                ))

    # Add sequential fallthrough edges between consecutive paragraphs
    para_names = [p.name for p in ast.paragraphs]
    for i in range(len(para_names) - 1):
        curr = para_names[i]
        nxt = para_names[i + 1]
        if curr in paragraph_block_ids and nxt in paragraph_block_ids:
            # Get last block of current paragraph
            curr_blocks = [
                b for b in blocks if b.paragraph == curr
            ]
            if curr_blocks:
                last_block = curr_blocks[-1]
                # Don't add fallthrough if last block exits
                has_exit = any(
                    t in _EXIT_TYPES for t in last_block.statement_types
                )
                if not has_exit:
                    edges.append(CFGEdge(
                        from_block=last_block.block_id,
                        to_block=paragraph_block_ids[nxt],
                        edge_type="fallthrough",
                    ))

    entry_block = blocks[0].block_id if blocks else None

    return ControlFlowGraph(
        program_id=ast.program_id or "",
        file_path=ast.file_path,
        blocks=blocks,
        edges=edges,
        entry_block=entry_block,
        exit_blocks=exit_blocks,
        perform_targets=perform_targets,
        unsupported_constructs=sorted(unsupported),
    )


def _build_paragraph_blocks(
    para_name: str,
    statements: list[StatementOut],
) -> tuple[list[CFGBlock], list[CFGEdge], set[str]]:
    """Split a paragraph's statements into basic blocks at branch points."""
    blocks: list[CFGBlock] = []
    edges: list[CFGEdge] = []
    unsupported: set[str] = set()
    current_types: list[str] = []
    block_counter = 0

    def _flush_block(entry_type: str = "entry") -> str:
        nonlocal block_counter
        bid = f"{para_name}:B{block_counter}"
        blocks.append(CFGBlock(
            block_id=bid,
            paragraph=para_name,
            statement_types=list(current_types),
            entry_type=entry_type,
        ))
        block_counter += 1
        current_types.clear()
        return bid

    for stmt in statements:
        if stmt.type in _UNSUPPORTED_TYPES:
            label = stmt.type.replace("-", " ")
            unsupported.add(label)

        if stmt.type in _BRANCH_TYPES:
            # Flush any accumulated statements as a block
            if current_types:
                prev_bid = _flush_block(
                    "entry" if block_counter == 0 else "sequential",
                )
            else:
                prev_bid = None

            # Create a block for the branch itself
            current_types.append(stmt.type)
            branch_bid = _flush_block(
                "entry" if block_counter == 1 and prev_bid is None
                else "sequential",
            )

            if prev_bid:
                edges.append(CFGEdge(
                    from_block=prev_bid,
                    to_block=branch_bid,
                    edge_type="sequential",
                ))

            # Create blocks for branch children (true/false or WHEN clauses)
            child_bids = []
            for i, child in enumerate(stmt.children):
                child_types = _collect_statement_types(child)
                if child_types:
                    if stmt.type == "IF":
                        etype = "branch_true" if i == 0 else "branch_false"
                    else:
                        etype = "branch_true"
                    cbid = f"{para_name}:B{block_counter}"
                    blocks.append(CFGBlock(
                        block_id=cbid,
                        paragraph=para_name,
                        statement_types=child_types,
                        entry_type=etype,
                    ))
                    block_counter += 1
                    child_bids.append(cbid)

                    edge_type = etype
                    edges.append(CFGEdge(
                        from_block=branch_bid,
                        to_block=cbid,
                        edge_type=edge_type,
                        condition=stmt.condition if i == 0 else None,
                    ))
        else:
            current_types.append(stmt.type)

    # Flush remaining statements
    if current_types:
        bid = _flush_block(
            "entry" if block_counter == 0 else "sequential",
        )
        # Connect to previous block if needed
        if blocks and len(blocks) >= 2:
            prev = blocks[-2]
            if prev.paragraph == para_name and prev.entry_type not in (
                "branch_true", "branch_false"
            ):
                already_connected = any(
                    e.from_block == prev.block_id and e.to_block == bid
                    for e in edges
                )
                if not already_connected:
                    edges.append(CFGEdge(
                        from_block=prev.block_id,
                        to_block=bid,
                        edge_type="sequential",
                    ))

    # If paragraph had no statements, create an empty entry block
    if not blocks:
        blocks.append(CFGBlock(
            block_id=f"{para_name}:B0",
            paragraph=para_name,
            statement_types=[],
            entry_type="entry",
        ))

    return blocks, edges, unsupported


def _collect_statement_types(stmt: StatementOut) -> list[str]:
    """Collect all statement types from a statement and its children."""
    types = [stmt.type]
    for child in stmt.children:
        types.extend(_collect_statement_types(child))
    return types


def _flatten_statements(
    statements: list[StatementOut],
) -> list[StatementOut]:
    """Flatten nested statement tree into a flat list."""
    result: list[StatementOut] = []
    for stmt in statements:
        result.append(stmt)
        result.extend(_flatten_statements(stmt.children))
    return result
