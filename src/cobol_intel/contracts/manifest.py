"""Manifest schema — the root artifact for every analysis run."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from cobol_intel.contracts.governance import GovernanceSummary


SCHEMA_VERSION = "1.0"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


class RunError(BaseModel):
    file: str
    module: str
    message: str
    line: int | None = None


class ArtifactIndex(BaseModel):
    ast: list[str] = Field(default_factory=list)
    graphs: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    docs: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    schema_version: str = SCHEMA_VERSION
    tool_version: str
    run_id: str
    project_name: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None = None
    input_paths: list[str]
    artifacts: ArtifactIndex = Field(default_factory=ArtifactIndex)
    warnings: list[str] = Field(default_factory=list)
    errors: list[RunError] = Field(default_factory=list)
    governance: GovernanceSummary = Field(default_factory=GovernanceSummary)

    def is_success(self) -> bool:
        return self.status == RunStatus.COMPLETED

    def has_errors(self) -> bool:
        return len(self.errors) > 0
