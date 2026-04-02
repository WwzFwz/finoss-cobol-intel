"""Integration tests for the REST API using FastAPI TestClient."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from cobol_intel.api.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"
RUNTIME_DIR = REPO_ROOT / "tests_runtime_api"

app = create_app()
client = TestClient(app)


def setup_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def teardown_module(module) -> None:
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_version_endpoint():
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["api_version"] == "v1"


def test_analyze_run_lifecycle():
    # Create analysis run
    response = client.post("/api/v1/runs/analyze", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
    })
    assert response.status_code == 201
    data = response.json()
    run_id = data["run_id"]
    assert data["status"] in ("completed", "partially_completed")
    assert "finished_at" in data
    assert "warning_count" in data
    assert "program_count" in data
    assert "error_count" in data

    # List runs
    response = client.get("/api/v1/runs", params={"output_dir": str(RUNTIME_DIR)})
    assert response.status_code == 200
    runs = response.json()
    assert runs["total"] >= 1
    assert runs["limit"] == 50
    assert runs["offset"] == 0
    assert any(r["run_id"] == run_id for r in runs["runs"])

    # Get specific run manifest
    response = client.get(f"/api/v1/runs/{run_id}", params={"output_dir": str(RUNTIME_DIR)})
    assert response.status_code == 200
    manifest = response.json()
    assert manifest["run_id"] == run_id
    assert manifest["schema_version"] == "1.0"

    response = client.get(f"/api/v1/runs/{run_id}/metrics", params={"output_dir": str(RUNTIME_DIR)})
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["run_id"] == run_id
    assert metrics["phase"] == "analysis"


def test_get_artifact_from_run():
    # Create a run first
    response = client.post("/api/v1/runs/analyze", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
    })
    data = response.json()
    run_id = data["run_id"]

    # Fetch the manifest as artifact
    response = client.get(
        f"/api/v1/runs/{run_id}/artifacts/manifest.json",
        params={"output_dir": str(RUNTIME_DIR)},
    )
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id


def test_get_audit_log():
    response = client.post("/api/v1/runs/analyze", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
    })
    run_id = response.json()["run_id"]

    response = client.get(
        f"/api/v1/runs/{run_id}/audit-log",
        params={"output_dir": str(RUNTIME_DIR)},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1


def test_analyze_returns_400_for_bad_path():
    response = client.post("/api/v1/runs/analyze", json={
        "path": "/nonexistent/path.cbl",
        "output_dir": str(RUNTIME_DIR),
    })
    assert response.status_code == 400
    assert response.json()["error_code"] == "E6001"
    assert response.json()["message"] == "Invalid analysis request"


def test_get_run_returns_404_for_unknown_id():
    response = client.get("/api/v1/runs/run_nonexistent", params={"output_dir": str(RUNTIME_DIR)})
    assert response.status_code == 404
    assert response.json()["error_code"] == "E5001"


def test_unknown_backend_returns_structured_error():
    response = client.post("/api/v1/runs/explain", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
        "backend": "unknown",
    })
    assert response.status_code == 400
    assert response.json()["error_code"] == "E6001"
    assert response.json()["message"] == "Unknown backend"


def test_list_runs_supports_pagination_and_status_filter():
    first = client.post("/api/v1/runs/analyze", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
    })
    second = client.post("/api/v1/runs/analyze", json={
        "path": str(SAMPLES_DIR / "complex" / "payment.cbl"),
        "output_dir": str(RUNTIME_DIR),
    })
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/api/v1/runs",
        params={
            "output_dir": str(RUNTIME_DIR),
            "status": "completed",
            "limit": 1,
            "offset": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert payload["total"] >= 2
    assert len(payload["runs"]) <= 1


def test_openapi_docs_available():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "cobol-intel"
