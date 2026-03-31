"""Business rules output contract — versioned schema for extracted rules JSON.

Written to artifacts/<run>/rules/<program>.json.
See ADR-007 in docs/DECISIONS.md.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from cobol_intel.contracts.source_ref import SourceRef

SCHEMA_VERSION = "1.0"


class BusinessRule(BaseModel):
    """A single extracted business rule from COBOL source."""

    rule_id: str
    type: str  # IF, EVALUATE, CONDITION-88
    condition: str
    actions: list[str] = Field(default_factory=list)
    paragraph: str | None = None
    source: SourceRef | None = None


class RulesOutput(BaseModel):
    """Root business rules artifact for a single COBOL program."""

    schema_version: str = SCHEMA_VERSION
    program_id: str | None = None
    file_path: str = ""
    rules: list[BusinessRule] = Field(default_factory=list)
