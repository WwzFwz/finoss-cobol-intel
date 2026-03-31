"""AST output contract — versioned schema for parser artifact JSON.

This is the serializable output written to artifacts/<run>/ast/<program>.json.
Parser-internal dataclasses (parsers.base) are converted to this contract
before writing to disk.

See ADR-007 in docs/DECISIONS.md.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from cobol_intel.contracts.source_ref import SourceRef

SCHEMA_VERSION = "1.0"


class StatementOut(BaseModel):
    """Serializable statement node."""

    type: str
    raw: str = ""
    target: str | None = None
    condition: str | None = None
    children: list[StatementOut] = Field(default_factory=list)
    source: SourceRef | None = None


class ParagraphOut(BaseModel):
    """Serializable paragraph node."""

    name: str
    statements: list[StatementOut] = Field(default_factory=list)
    source: SourceRef | None = None


class DataItemOut(BaseModel):
    """Serializable data item node."""

    level: int
    name: str
    pic: str | None = None
    usage: str | None = None
    value: str | None = None
    redefines: str | None = None
    occurs: int | None = None
    is_condition: bool = False
    condition_values: list[str] = Field(default_factory=list)
    children: list[DataItemOut] = Field(default_factory=list)
    source: SourceRef | None = None


class ASTOutput(BaseModel):
    """Root AST artifact for a single COBOL program."""

    schema_version: str = SCHEMA_VERSION
    program_id: str | None = None
    file_path: str = ""
    parser_name: str = ""
    data_items: list[DataItemOut] = Field(default_factory=list)
    paragraphs: list[ParagraphOut] = Field(default_factory=list)
    copybooks_used: list[str] = Field(default_factory=list)
