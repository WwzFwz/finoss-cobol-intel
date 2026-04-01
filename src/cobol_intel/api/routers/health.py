"""Health and version endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from cobol_intel import __version__
from cobol_intel.api.constants import API_VERSION
from cobol_intel.api.models import HealthResponse, VersionResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(version=__version__, api_version=API_VERSION)
