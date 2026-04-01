"""Consistent API error helpers and exception type."""

from __future__ import annotations

from dataclasses import dataclass

from cobol_intel.contracts.manifest import ErrorCode


@dataclass
class ApiError(Exception):
    """Structured API exception rendered by the FastAPI app handler."""

    status_code: int
    error_code: str
    message: str
    detail: str | None = None


def api_error(
    status_code: int,
    error_code: ErrorCode | str,
    message: str,
    detail: str | None = None,
) -> ApiError:
    """Build an ApiError with a stable string error code."""
    return ApiError(
        status_code=status_code,
        error_code=error_code.value if isinstance(error_code, ErrorCode) else error_code,
        message=message,
        detail=detail,
    )
