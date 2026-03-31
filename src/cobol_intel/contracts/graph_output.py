"""Call graph output contract — versioned schema for dependency artifact JSON.

Written to artifacts/<run>/graphs/call_graph.json.
See ADR-007 in docs/DECISIONS.md.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class CallEdge(BaseModel):
    """A single CALL relationship: caller -> callee."""

    caller: str
    callee: str
    call_type: str = "STATIC"  # STATIC or DYNAMIC


class CallGraphOutput(BaseModel):
    """Root call graph artifact."""

    schema_version: str = SCHEMA_VERSION
    nodes: list[str] = Field(default_factory=list)
    edges: list[CallEdge] = Field(default_factory=list)
    adjacency: dict[str, list[str]] = Field(default_factory=dict)
    entry_points: list[str] = Field(default_factory=list)
    external_calls: list[str] = Field(default_factory=list)

    def to_mermaid(self) -> str:
        """Render graph as Mermaid flowchart."""
        lines = ["graph TD"]
        for edge in self.edges:
            lines.append(f"    {edge.caller} --> {edge.callee}")
        for ext in self.external_calls:
            lines.append(f"    {ext}[/{ext}/]")
        if not self.edges:
            for node in self.nodes:
                lines.append(f"    {node}")
        return "\n".join(lines)
