"""Artifact writers and lightweight report renderers for Phase 1 outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.manifest import Manifest
from cobol_intel.contracts.rules_output import RulesOutput


def ensure_directory(path: Path) -> Path:
    """Create a directory tree if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json_artifact(path: Path, artifact: BaseModel | dict[str, Any]) -> Path:
    """Write a Pydantic model or JSON-like dict to disk."""
    ensure_directory(path.parent)
    payload = artifact.model_dump(mode="json") if isinstance(artifact, BaseModel) else artifact
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_jsonl_artifact(path: Path, artifact: BaseModel | dict[str, Any]) -> Path:
    """Append one JSON object per line to a JSONL artifact."""
    ensure_directory(path.parent)
    payload = artifact.model_dump(mode="json") if isinstance(artifact, BaseModel) else artifact
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return path


def write_text_artifact(path: Path, content: str) -> Path:
    """Write plain-text artifact to disk."""
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def render_rules_markdown(rules_output: RulesOutput) -> str:
    """Render extracted business rules as a small Markdown report."""
    title = rules_output.program_id or Path(rules_output.file_path).stem or "UNKNOWN"
    lines = [f"# Rules - {title}", ""]

    if not rules_output.rules:
        lines.extend(["No business rules extracted.", ""])
        return "\n".join(lines)

    for rule in rules_output.rules:
        lines.append(f"## {rule.rule_id} - {rule.type}")
        lines.append(f"- Condition: `{rule.condition}`")
        if rule.paragraph:
            lines.append(f"- Paragraph: `{rule.paragraph}`")
        if rule.actions:
            lines.append(f"- Actions: {', '.join(f'`{action}`' for action in rule.actions)}")
        if rule.source:
            lines.append(f"- Source: `{rule.source.file}`")
        lines.append("")

    return "\n".join(lines)


def render_summary_markdown(
    manifest: Manifest,
    rules_by_program: list[RulesOutput],
    call_graph: CallGraphOutput,
) -> str:
    """Render a human-readable summary for one analysis run."""
    lines = [
        f"# Analysis Summary - {manifest.project_name}",
        "",
        f"- Run ID: `{manifest.run_id}`",
        f"- Status: `{manifest.status.value}`",
        f"- Programs: `{len(manifest.artifacts.ast)}`",
        f"- Rules files: `{len(manifest.artifacts.rules)}`",
        f"- Graph edges: `{len(call_graph.edges)}`",
        "",
        "## Programs",
        "",
    ]

    if not rules_by_program:
        lines.extend(["No program summaries available.", ""])
    else:
        for rules_output in rules_by_program:
            program_id = rules_output.program_id or Path(rules_output.file_path).stem or "UNKNOWN"
            lines.append(
                f"- `{program_id}`: {len(rules_output.rules)} extracted rule(s)"
            )
        lines.append("")

    lines.extend(
        [
            "## Call Graph",
            "",
            "```mermaid",
            call_graph.to_mermaid(),
            "```",
            "",
        ]
    )

    return "\n".join(lines)
