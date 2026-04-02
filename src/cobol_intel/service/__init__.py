"""
service: Pipeline orchestration, run lifecycle, and artifact writer.

This is the single entry point for CLI, API, and future GUI.

Rules:
- CLI and future interfaces must go through service, not call parsers/analysis directly.
- Manages run lifecycle: queued -> running -> completed/partially_completed/failed.
- Writes artifacts to filesystem under artifacts/<project_slug>/<run_id>/.
"""

from cobol_intel.service.explain import explain_path
from cobol_intel.service.pipeline import (
    AnalysisRunResult,
    analyze_path,
    discover_cobol_files,
    to_ast_output,
)

__all__ = [
    "AnalysisRunResult",
    "analyze_path",
    "discover_cobol_files",
    "explain_path",
    "to_ast_output",
]
