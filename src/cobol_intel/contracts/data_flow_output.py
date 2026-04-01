"""Data flow graph output contract — field-level read/write tracking.

Written to artifacts/<run>/analysis/data_flow.json.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class FlowType(str, Enum):
    MOVE = "move"
    COMPUTE = "compute"
    READ_INTO = "read_into"
    WRITE_FROM = "write_from"
    REWRITE_FROM = "rewrite_from"
    CALL_PARAM = "call_param"
    CONDITION_READ = "condition_read"


class DataFlowEdge(BaseModel):
    """A data flow edge between fields."""

    source_field: str
    target_field: str = ""
    flow_type: FlowType
    paragraph: str = ""
    program_id: str = ""
    statement_raw: str | None = None


class DataFlowGraph(BaseModel):
    """Per-program data flow graph."""

    schema_version: str = SCHEMA_VERSION
    program_id: str
    file_path: str = ""
    edges: list[DataFlowEdge] = Field(default_factory=list)
    field_read_count: dict[str, int] = Field(default_factory=dict)
    field_write_count: dict[str, int] = Field(default_factory=dict)
    entry_fields: list[str] = Field(default_factory=list)
    output_fields: list[str] = Field(default_factory=list)

    def to_mermaid(self) -> str:
        """Render data flow as a Mermaid flowchart."""
        lines = ["graph LR"]
        seen: set[tuple[str, str]] = set()
        for edge in self.edges:
            src = edge.source_field
            tgt = edge.target_field or f"{edge.flow_type.value}_sink"
            pair = (src, tgt)
            if pair not in seen:
                seen.add(pair)
                label = edge.flow_type.value.upper()
                lines.append(f"    {src} -->|{label}| {tgt}")

        for field in self.entry_fields:
            lines.append(f"    {field}[/{field}/]")
        for field in self.output_fields:
            lines.append(f"    {field}[\\{field}\\]")

        if not self.edges and not self.entry_fields:
            lines.append("    empty[No data flow detected]")
        return "\n".join(lines)
