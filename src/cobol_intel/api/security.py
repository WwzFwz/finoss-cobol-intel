"""Security helpers for the API layer."""

from __future__ import annotations

from pathlib import Path

from cobol_intel.api.errors import api_error
from cobol_intel.contracts.manifest import ErrorCode


def safe_artifact_path(run_dir: Path, artifact_path: str) -> Path:
    """Resolve artifact path with path traversal prevention.

    Raises HTTPException(400) if the resolved path escapes run_dir.
    """
    resolved = (run_dir / artifact_path).resolve()
    if not resolved.is_relative_to(run_dir.resolve()):
        raise api_error(
            400,
            ErrorCode.CONFIG_INVALID,
            "Invalid artifact path",
            "Path traversal detected",
        )
    if not resolved.exists():
        raise api_error(
            404,
            ErrorCode.IO_WRITE,
            "Artifact not found",
            f"Artifact not found: {artifact_path}",
        )
    return resolved
