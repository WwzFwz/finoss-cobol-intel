"""Unit tests for API request/response models."""

from cobol_intel.api.models import (
    AnalyzeRequest,
    ErrorResponse,
    ExplainRequest,
    HealthResponse,
    RunListResponse,
    RunSummary,
    VersionResponse,
)


def test_analyze_request_defaults():
    req = AnalyzeRequest(path="samples/")
    assert req.output_dir == "artifacts"
    assert req.copybook_dirs == []


def test_explain_request_defaults():
    req = ExplainRequest(path="samples/")
    assert req.backend == "claude"
    assert req.mode == "technical"
    assert req.strict_policy is False
    assert req.max_tokens_per_run is None
    assert req.parallel is False
    assert req.max_workers is None
    assert req.cache is True


def test_error_response_serializes():
    resp = ErrorResponse(error_code="E3001", message="LLM failed", detail="timeout after 30s")
    data = resp.model_dump()
    assert data["error_code"] == "E3001"


def test_run_list_response():
    run = RunSummary(
        run_id="run_001",
        project_name="demo",
        status="completed",
        started_at="2026-04-01T00:00:00Z",
        finished_at="2026-04-01T00:00:01Z",
        artifacts_dir="artifacts/demo/run_001",
        duration_ms=1000,
        warning_count=1,
        program_count=2,
        error_count=0,
    )
    resp = RunListResponse(runs=[run], total=1, limit=50, offset=0)
    assert resp.total == 1


def test_health_response():
    resp = HealthResponse(status="ok", version="0.1.0")
    assert resp.status == "ok"


def test_version_response():
    resp = VersionResponse(version="0.2.0", api_version="v1")
    assert resp.api_version == "v1"
