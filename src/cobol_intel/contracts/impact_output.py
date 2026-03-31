"""Change impact analysis output contract."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class ImpactType(str, Enum):
    DIRECT_CALLER = "direct_caller"
    TRANSITIVE_CALLER = "transitive_caller"
    SHARED_COPYBOOK = "shared_copybook"
    FIELD_REFERENCE = "field_reference"


class ImpactedEntity(BaseModel):
    program_id: str
    file_path: str = ""
    impact_type: ImpactType
    distance: int = 0
    affected_paragraphs: list[str] = Field(default_factory=list)
    affected_rules: list[str] = Field(default_factory=list)
    reason: str = ""


class ImpactReport(BaseModel):
    schema_version: str = SCHEMA_VERSION
    changed_programs: list[str] = Field(default_factory=list)
    changed_fields: list[str] = Field(default_factory=list)
    impacted_entities: list[ImpactedEntity] = Field(default_factory=list)
    total_impacted: int = 0
    analysis_run_id: str = ""
