"""Dead code detection output contract.

Written to artifacts/<run>/analysis/dead_code.json.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class DeadCodeType(str, Enum):
    UNREACHABLE_PARAGRAPH = "unreachable_paragraph"
    UNUSED_DATA_ITEM = "unused_data_item"
    DEAD_BRANCH = "dead_branch"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"


class DeadCodeItem(BaseModel):
    """A single dead code finding."""

    type: DeadCodeType
    name: str
    file_path: str = ""
    program_id: str = ""
    reason: str = ""
    confidence: Confidence = Confidence.HIGH


class DeadCodeReport(BaseModel):
    """Dead code analysis report for a single program."""

    schema_version: str = SCHEMA_VERSION
    program_id: str
    file_path: str = ""
    items: list[DeadCodeItem] = Field(default_factory=list)
    total_dead: int = 0
    total_lines_dead: int = 0
    dead_code_percentage: float = 0.0
    warnings: list[str] = Field(default_factory=list)
