"""FastAPI application factory for cobol-intel."""

from __future__ import annotations

from fastapi import FastAPI

from cobol_intel import __version__
from cobol_intel.api.routers import artifacts, health, runs


def create_app() -> FastAPI:
    """Create the cobol-intel REST API application."""
    app = FastAPI(
        title="cobol-intel",
        description="Read-only REST API for consuming COBOL analysis artifacts.",
        version=__version__,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")
    app.include_router(artifacts.router, prefix="/api/v1")
    return app


def main() -> None:
    """Entrypoint for the cobol-intel-api console script."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
