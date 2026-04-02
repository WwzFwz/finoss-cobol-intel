"""Versioned run metrics contract for observability and API consumption."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

SCHEMA_VERSION = "1.0"


class RunMetrics(BaseModel):
    """Stable per-run metrics artifact written to metrics/run_metrics.json."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    phase: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int = 0
    files_total: int = 0
    files_successful: int = 0
    files_failed: int = 0
    warning_count: int = 0
    error_count: int = 0
    backend: str | None = None
    model: str | None = None
    retry_count: int = 0
    timeout_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    token_usage_total: int = 0
    policy_violation_count: int = 0
    budget_exhausted: bool = False
