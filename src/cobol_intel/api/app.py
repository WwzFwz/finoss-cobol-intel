"""FastAPI application factory for cobol-intel."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cobol_intel import __version__
from cobol_intel.api.constants import API_PREFIX
from cobol_intel.api.errors import ApiError
from cobol_intel.api.models import ErrorResponse
from cobol_intel.api.routers import artifacts, health, runs


def create_app() -> FastAPI:
    """Create the cobol-intel REST API application."""
    app = FastAPI(
        title="cobol-intel",
        description="Versioned REST API for consuming COBOL analysis artifacts and runs.",
        version=__version__,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                detail=exc.detail,
            ).model_dump(),
        )

    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(runs.router, prefix=API_PREFIX)
    app.include_router(artifacts.router, prefix=API_PREFIX)
    return app


app = create_app()


def main() -> None:
    """Entrypoint for the cobol-intel-api console script."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
