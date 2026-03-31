"""Explanation output contract — versioned schema for LLM-generated explanations.

Written to artifacts/<run>/docs/<program>_explanation.json.
See ADR-007 in docs/DECISIONS.md.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from cobol_intel.contracts.source_ref import SourceRef

SCHEMA_VERSION = "1.0"


class ExplanationMode(str, Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    AUDIT = "audit"


class ParagraphExplanation(BaseModel):
    """Explanation for a single paragraph."""

    paragraph: str
    summary: str
    details: str = ""
    source: SourceRef | None = None


class ExplanationOutput(BaseModel):
    """Root explanation artifact for a single COBOL program."""

    schema_version: str = SCHEMA_VERSION
    program_id: str | None = None
    file_path: str = ""
    mode: ExplanationMode = ExplanationMode.TECHNICAL
    backend: str = ""
    model: str = ""
    program_summary: str = ""
    program_summary_sources: list[SourceRef] = Field(default_factory=list)
    paragraph_explanations: list[ParagraphExplanation] = Field(default_factory=list)
    data_summary: str = ""
    data_summary_sources: list[SourceRef] = Field(default_factory=list)
    business_rules_summary: str = ""
    business_rules_summary_sources: list[SourceRef] = Field(default_factory=list)
    paragraph_limit: int | None = None
    paragraphs_skipped: list[str] = Field(default_factory=list)
    tokens_used: int = 0
