"""Contract tests for Manifest schema."""

from datetime import datetime, timezone

import pytest

from cobol_intel.contracts.manifest import ArtifactIndex, Manifest, RunError, RunStatus


def make_manifest(**kwargs) -> Manifest:
    defaults = {
        "tool_version": "0.1.0",
        "run_id": "run_20260331_001",
        "project_name": "test-project",
        "status": RunStatus.COMPLETED,
        "started_at": datetime(2026, 3, 31, 10, 0, 0, tzinfo=timezone.utc),
        "input_paths": ["samples/CALCINT.cbl"],
    }
    return Manifest(**{**defaults, **kwargs})


def test_manifest_schema_version_is_always_present():
    m = make_manifest()
    assert m.schema_version == "1.0"


def test_manifest_completed_has_no_errors():
    m = make_manifest(status=RunStatus.COMPLETED)
    assert m.is_success()
    assert not m.has_errors()


def test_manifest_partial_with_errors():
    error = RunError(file="LEGACY.cbl", module="parser", message="Unsupported dialect", line=42)
    m = make_manifest(status=RunStatus.PARTIALLY_COMPLETED, errors=[error])
    assert not m.is_success()
    assert m.has_errors()


def test_manifest_serializes_to_dict_with_required_fields():
    m = make_manifest()
    data = m.model_dump()
    required = {"schema_version", "tool_version", "run_id", "project_name", "status",
                "started_at", "input_paths", "artifacts", "warnings", "errors", "governance"}
    assert required.issubset(data.keys())


def test_manifest_artifact_index_starts_empty():
    m = make_manifest()
    assert m.artifacts.ast == []
    assert m.artifacts.graphs == []
    assert m.artifacts.rules == []
    assert m.artifacts.logs == []


def test_manifest_governance_defaults_exist():
    m = make_manifest()
    assert m.governance.data_sensitivity.value == "low"
    assert m.governance.token_usage.requests == 0
