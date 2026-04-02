"""Contract tests for the RunMetrics schema."""

from __future__ import annotations

from datetime import datetime, timezone

from cobol_intel.contracts.run_metrics import RunMetrics


def test_run_metrics_has_schema_version():
    metrics = RunMetrics(
        run_id="run_001",
        phase="analysis",
        started_at=datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc),
    )
    assert metrics.schema_version == "1.0"


def test_run_metrics_serializes_required_enterprise_fields():
    metrics = RunMetrics(
        run_id="run_001",
        phase="explain",
        started_at=datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 4, 3, 0, 1, tzinfo=timezone.utc),
        duration_ms=60000,
        files_total=3,
        files_successful=2,
        files_failed=1,
        warning_count=4,
        error_count=1,
        backend="openai",
        model="gpt-5-mini",
        retry_count=2,
        timeout_count=1,
        cache_hits=1,
        cache_misses=2,
        token_usage_total=1234,
        policy_violation_count=1,
        budget_exhausted=True,
    )

    data = metrics.model_dump()
    assert data["backend"] == "openai"
    assert data["retry_count"] == 2
    assert data["cache_hits"] == 1
    assert data["budget_exhausted"] is True
