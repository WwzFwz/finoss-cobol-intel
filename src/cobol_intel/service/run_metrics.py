"""Helpers for building and writing stable run metrics artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cobol_intel.contracts.manifest import Manifest
from cobol_intel.contracts.run_metrics import RunMetrics
from cobol_intel.outputs import write_json_artifact

_RUN_METRICS_REL_PATH = Path("metrics") / "run_metrics.json"


def build_run_metrics(
    manifest: Manifest,
    *,
    phase: str,
    files_total: int,
    files_successful: int,
    files_failed: int,
    backend: str | None = None,
    model: str | None = None,
    retry_count: int = 0,
    timeout_count: int = 0,
    cache_hits: int = 0,
    cache_misses: int = 0,
    token_usage_total: int = 0,
    policy_violation_count: int = 0,
    budget_exhausted: bool = False,
) -> RunMetrics:
    """Build a stable metrics snapshot from the manifest and counters."""
    finished_at = manifest.finished_at
    return RunMetrics(
        run_id=manifest.run_id,
        phase=phase,
        started_at=manifest.started_at,
        finished_at=finished_at,
        duration_ms=_duration_ms(manifest.started_at, finished_at),
        files_total=files_total,
        files_successful=files_successful,
        files_failed=files_failed,
        warning_count=len(manifest.warnings),
        error_count=len(manifest.errors),
        backend=backend,
        model=model,
        retry_count=retry_count,
        timeout_count=timeout_count,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        token_usage_total=token_usage_total,
        policy_violation_count=policy_violation_count,
        budget_exhausted=budget_exhausted,
    )


def write_run_metrics(run_dir: Path, manifest: Manifest, metrics: RunMetrics) -> Path:
    """Write metrics/run_metrics.json and register it on the manifest."""
    rel_path = _RUN_METRICS_REL_PATH.as_posix()
    if rel_path not in manifest.artifacts.metrics:
        manifest.artifacts.metrics.append(rel_path)
    return write_json_artifact(run_dir / _RUN_METRICS_REL_PATH, metrics)


def _duration_ms(started_at: datetime, finished_at: datetime | None) -> int:
    if finished_at is None:
        return 0
    return max(0, int((finished_at - started_at).total_seconds() * 1000))
