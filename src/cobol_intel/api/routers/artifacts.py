"""Artifact serving endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from cobol_intel.api.security import safe_artifact_path

router = APIRouter(tags=["artifacts"])


@router.get("/runs/{run_id}/artifacts/{artifact_path:path}")
def get_artifact(run_id: str, artifact_path: str, output_dir: str = "artifacts"):
    """Serve an artifact file from a completed run."""
    run_dir = _find_run_dir(run_id, Path(output_dir))
    if run_dir is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    resolved = safe_artifact_path(run_dir, artifact_path)

    if resolved.suffix == ".json":
        data = json.loads(resolved.read_text(encoding="utf-8"))
        return JSONResponse(content=data)

    return FileResponse(path=str(resolved), filename=resolved.name)


@router.get("/runs/{run_id}/audit-log")
def get_audit_log(run_id: str, output_dir: str = "artifacts"):
    """Return audit events for a run as a JSON array."""
    run_dir = _find_run_dir(run_id, Path(output_dir))
    if run_dir is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    log_path = run_dir / "logs" / "audit_events.jsonl"
    if not log_path.exists():
        return JSONResponse(content=[])

    events = []
    for line in log_path.read_text(encoding="utf-8").strip().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return JSONResponse(content=events)


def _find_run_dir(run_id: str, artifacts_root: Path) -> Path | None:
    if not artifacts_root.exists():
        return None
    for project_dir in artifacts_root.iterdir():
        if not project_dir.is_dir():
            continue
        run_dir = project_dir / run_id
        if run_dir.is_dir():
            return run_dir
    return None
