"""
outputs: Artifact formatters and report generators.

Formats: Markdown, JSON, HTML, Mermaid.

Rules:
- No parsing logic.
- No LLM calls.
- Consumes contracts artifacts, produces files.
"""

from cobol_intel.outputs.writers import (
    ensure_directory,
    render_rules_markdown,
    render_summary_markdown,
    write_json_artifact,
    write_jsonl_artifact,
    write_text_artifact,
)
from cobol_intel.outputs.doc_generator import (
    ProgramDocumentation,
    generate_program_doc,
    generate_project_report,
)

__all__ = [
    "ensure_directory",
    "render_rules_markdown",
    "render_summary_markdown",
    "write_json_artifact",
    "write_jsonl_artifact",
    "write_text_artifact",
    "ProgramDocumentation",
    "generate_program_doc",
    "generate_project_report",
]
