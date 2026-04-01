"""API request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    path: str
    output_dir: str = "artifacts"
    copybook_dirs: list[str] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    path: str
    backend: str = "claude"
    mode: str = "technical"
    output_dir: str = "artifacts"
    copybook_dirs: list[str] = Field(default_factory=list)
    policy_config_path: str | None = None
    strict_policy: bool = False
    max_tokens_per_run: int | None = None


class RunSummary(BaseModel):
    run_id: str
    project_name: str
    status: str
    started_at: str
    artifacts_dir: str
    program_count: int = 0
    error_count: int = 0


class RunListResponse(BaseModel):
    runs: list[RunSummary]
    total: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


class VersionResponse(BaseModel):
    version: str
    api_version: str
