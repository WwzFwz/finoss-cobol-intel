"""Control flow graph output contract — intra-program CFG for semantic analysis.

Written to artifacts/<run>/graphs/control_flow_graph.json.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class CFGBlock(BaseModel):
    """A basic block in the control flow graph."""

    block_id: str
    paragraph: str
    statement_types: list[str] = Field(default_factory=list)
    entry_type: str = "entry"


class CFGEdge(BaseModel):
    """A control flow edge between blocks."""

    from_block: str
    to_block: str
    edge_type: str = "sequential"
    condition: str | None = None


class ControlFlowGraph(BaseModel):
    """Intra-program control flow graph."""

    schema_version: str = SCHEMA_VERSION
    program_id: str
    file_path: str = ""
    blocks: list[CFGBlock] = Field(default_factory=list)
    edges: list[CFGEdge] = Field(default_factory=list)
    entry_block: str | None = None
    exit_blocks: list[str] = Field(default_factory=list)
    perform_targets: dict[str, list[str]] = Field(default_factory=dict)
    unsupported_constructs: list[str] = Field(default_factory=list)
