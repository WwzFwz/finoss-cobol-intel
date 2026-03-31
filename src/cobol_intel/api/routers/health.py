"""Health and version endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from cobol_intel import __version__
from cobol_intel.api.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}
