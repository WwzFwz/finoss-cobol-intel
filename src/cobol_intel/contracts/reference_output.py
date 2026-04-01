"""Field reference index output contract — read/write/condition classification.

Written to artifacts/<run>/analysis/reference_index.json.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class ReferenceType(str, Enum):
    READ = "read"
    WRITE = "write"
    CONDITION = "condition"
    CALL_PARAM = "call_param"


class FieldReference(BaseModel):
    """A single field reference in a statement."""

    field_name: str
    reference_type: ReferenceType
    paragraph: str
    statement_type: str
    statement_raw: str | None = None


class ReferenceIndex(BaseModel):
    """Per-program field reference index."""

    schema_version: str = SCHEMA_VERSION
    program_id: str
    file_path: str = ""
    references: list[FieldReference] = Field(default_factory=list)
    field_read_count: dict[str, int] = Field(default_factory=dict)
    field_write_count: dict[str, int] = Field(default_factory=dict)
    defined_fields: list[str] = Field(default_factory=list)
    entry_fields: list[str] = Field(default_factory=list)
    unsupported_constructs: list[str] = Field(default_factory=list)
