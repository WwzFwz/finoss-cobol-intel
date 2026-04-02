"""Run management endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from cobol_intel.api.errors import api_error
from cobol_intel.api.models import (
    AnalyzeRequest,
    ErrorResponse,
    ExplainRequest,
    RunListResponse,
    RunMetricsResponse,
    RunSummary,
)
from cobol_intel.contracts.manifest import ErrorCode, Manifest
from cobol_intel.contracts.run_metrics import RunMetrics

router = APIRouter(tags=["runs"])

_DEFAULT_ARTIFACTS_DIR = Path("artifacts")


@router.post(
    "/runs/analyze",
    response_model=RunSummary,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
def create_analysis_run(request: AnalyzeRequest) -> RunSummary:
    from cobol_intel.service.pipeline import analyze_path

    try:
        result = analyze_path(
            path=request.path,
            output_dir=request.output_dir,
            copybook_dirs=request.copybook_dirs or [],
        )
    except FileNotFoundError as exc:
        raise api_error(400, ErrorCode.CONFIG_INVALID, "Invalid analysis request", str(exc))

    return _to_run_summary(result.manifest, result.run_dir)


@router.post(
    "/runs/explain",
    response_model=RunSummary,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
def create_explain_run(request: ExplainRequest) -> RunSummary:
    from cobol_intel.contracts.explanation_output import ExplanationMode
    from cobol_intel.service.explain import explain_path

    backend = _resolve_backend(request.backend)
    try:
        result, _ = explain_path(
            path=request.path,
            backend=backend,
            mode=ExplanationMode(request.mode),
            output_dir=request.output_dir,
            copybook_dirs=request.copybook_dirs or [],
            policy_config_path=request.policy_config_path,
            strict_policy=request.strict_policy or None,
            max_tokens_per_run=request.max_tokens_per_run,
            parallel=request.parallel,
            max_workers=request.max_workers,
            use_cache=request.cache,
        )
    except FileNotFoundError as exc:
        raise api_error(400, ErrorCode.CONFIG_INVALID, "Invalid explain request", str(exc))

    return _to_run_summary(result.manifest, result.run_dir)


@router.get("/runs", response_model=RunListResponse)
def list_runs(
    project: str | None = None,
    output_dir: str = "artifacts",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
) -> RunListResponse:
    """List recent analysis runs by scanning the artifacts directory."""
    artifacts_root = Path(output_dir)
    if not artifacts_root.exists():
        return RunListResponse(runs=[], total=0, limit=limit, offset=offset)

    runs: list[RunSummary] = []
    project_dirs = [artifacts_root / project] if project else sorted(artifacts_root.iterdir())

    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue
        for run_dir in sorted(project_dir.iterdir(), reverse=True):
            manifest_path = run_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                manifest = Manifest(**json.loads(manifest_path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            if status is not None and manifest.status.value != status:
                continue
            runs.append(_to_run_summary(manifest, run_dir))

    total = len(runs)
    page = runs[offset: offset + limit]
    return RunListResponse(runs=page, total=total, limit=limit, offset=offset)


@router.get(
    "/runs/{run_id}",
    response_model=Manifest,
    responses={404: {"model": ErrorResponse}},
)
def get_run(run_id: str, output_dir: str = "artifacts") -> Manifest:
    """Get the full manifest for a specific run."""
    manifest_path = _find_manifest(run_id, Path(output_dir))
    if manifest_path is None:
        raise api_error(404, ErrorCode.IO_WRITE, "Run not found", f"Run not found: {run_id}")
    return Manifest(**json.loads(manifest_path.read_text(encoding="utf-8")))


@router.get(
    "/runs/{run_id}/metrics",
    response_model=RunMetricsResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_metrics(run_id: str, output_dir: str = "artifacts") -> RunMetricsResponse:
    """Get the stable metrics artifact for a specific run."""
    manifest_path = _find_manifest(run_id, Path(output_dir))
    if manifest_path is None:
        raise api_error(404, ErrorCode.IO_WRITE, "Run not found", f"Run not found: {run_id}")

    manifest = Manifest(**json.loads(manifest_path.read_text(encoding="utf-8")))
    metrics_rel = next(iter(manifest.artifacts.metrics), None)
    if metrics_rel is None:
        raise api_error(
            404,
            ErrorCode.IO_WRITE,
            "Run metrics not found",
            f"No metrics artifact registered for run: {run_id}",
        )

    metrics_path = manifest_path.parent / metrics_rel
    if not metrics_path.exists():
        raise api_error(
            404,
            ErrorCode.IO_WRITE,
            "Run metrics not found",
            f"Metrics artifact missing on disk for run: {run_id}",
        )

    metrics = RunMetrics(**json.loads(metrics_path.read_text(encoding="utf-8")))
    return RunMetricsResponse(**metrics.model_dump())


def _find_manifest(run_id: str, artifacts_root: Path) -> Path | None:
    """Find manifest.json for a given run_id by scanning project directories."""
    if not artifacts_root.exists():
        return None
    for project_dir in artifacts_root.iterdir():
        if not project_dir.is_dir():
            continue
        manifest_path = project_dir / run_id / "manifest.json"
        if manifest_path.exists():
            return manifest_path
    return None


def _resolve_backend(backend_name: str):
    """Resolve LLM backend by name."""
    if backend_name == "claude":
        from cobol_intel.llm.claude_backend import ClaudeBackend
        return ClaudeBackend()
    elif backend_name == "openai":
        from cobol_intel.llm.openai_backend import OpenAIBackend
        return OpenAIBackend()
    elif backend_name == "ollama":
        from cobol_intel.llm.ollama_backend import OllamaBackend
        return OllamaBackend()
    elif backend_name == "local":
        from cobol_intel.llm.local_backend import LocalBackend
        return LocalBackend()
    else:
        raise api_error(
            400,
            ErrorCode.CONFIG_INVALID,
            "Unknown backend",
            f"Unknown backend: {backend_name}",
        )


def _to_run_summary(manifest: Manifest, run_dir: Path) -> RunSummary:
    duration_ms = 0
    if manifest.finished_at is not None:
        duration_ms = max(
            0,
            int((manifest.finished_at - manifest.started_at).total_seconds() * 1000),
        )
    return RunSummary(
        run_id=manifest.run_id,
        project_name=manifest.project_name,
        status=manifest.status.value,
        started_at=manifest.started_at.isoformat(),
        finished_at=manifest.finished_at.isoformat() if manifest.finished_at else None,
        artifacts_dir=str(run_dir),
        duration_ms=duration_ms,
        warning_count=len(manifest.warnings),
        program_count=len(manifest.artifacts.ast),
        error_count=len(manifest.errors),
    )
