"""Run management endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from cobol_intel.api.models import (
    AnalyzeRequest,
    ErrorResponse,
    ExplainRequest,
    RunListResponse,
    RunSummary,
)
from cobol_intel.contracts.manifest import Manifest

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
        raise HTTPException(status_code=400, detail=str(exc))

    return RunSummary(
        run_id=result.manifest.run_id,
        project_name=result.manifest.project_name,
        status=result.manifest.status.value,
        started_at=result.manifest.started_at.isoformat(),
        artifacts_dir=str(result.run_dir),
    )


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
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RunSummary(
        run_id=result.manifest.run_id,
        project_name=result.manifest.project_name,
        status=result.manifest.status.value,
        started_at=result.manifest.started_at.isoformat(),
        artifacts_dir=str(result.run_dir),
    )


@router.get("/runs", response_model=RunListResponse)
def list_runs(
    project: str | None = None,
    output_dir: str = "artifacts",
    limit: int = 50,
) -> RunListResponse:
    """List recent analysis runs by scanning the artifacts directory."""
    artifacts_root = Path(output_dir)
    if not artifacts_root.exists():
        return RunListResponse(runs=[], total=0)

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
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                runs.append(RunSummary(
                    run_id=data["run_id"],
                    project_name=data["project_name"],
                    status=data["status"],
                    started_at=data["started_at"],
                    artifacts_dir=str(run_dir),
                ))
            except (json.JSONDecodeError, KeyError):
                continue
            if len(runs) >= limit:
                break
        if len(runs) >= limit:
            break

    return RunListResponse(runs=runs, total=len(runs))


@router.get("/runs/{run_id}")
def get_run(run_id: str, output_dir: str = "artifacts") -> dict:
    """Get the full manifest for a specific run."""
    manifest_path = _find_manifest(run_id, Path(output_dir))
    if manifest_path is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


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
    else:
        raise HTTPException(status_code=400, detail=f"Unknown backend: {backend_name}")
