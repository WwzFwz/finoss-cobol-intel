"""Documentation generation service — reads artifacts from a completed run."""

from __future__ import annotations

import json
from pathlib import Path

from cobol_intel.contracts.ast_output import ASTOutput
from cobol_intel.contracts.explanation_output import ExplanationOutput
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.manifest import Manifest
from cobol_intel.contracts.rules_output import RulesOutput
from cobol_intel.outputs import write_text_artifact
from cobol_intel.outputs.doc_generator import (
    ProgramDocumentation,
    generate_program_doc,
    generate_project_report,
)


def generate_docs(run_dir: Path) -> list[Path]:
    """Read artifacts from a completed run and generate documentation.

    Returns list of generated doc file paths.
    """
    manifest_path = run_dir / "manifest.json"
    manifest = Manifest(**json.loads(manifest_path.read_text(encoding="utf-8")))

    # Load call graph
    call_graph = None
    for graph_rel in manifest.artifacts.graphs:
        if "call_graph.json" in graph_rel:
            graph_path = run_dir / graph_rel
            if graph_path.exists():
                call_graph = CallGraphOutput(**json.loads(graph_path.read_text(encoding="utf-8")))
                break

    # Load ASTs, rules, and explanations per program
    asts: dict[str, ASTOutput] = {}
    for ast_rel in manifest.artifacts.ast:
        ast_path = run_dir / ast_rel
        if ast_path.exists():
            ast = ASTOutput(**json.loads(ast_path.read_text(encoding="utf-8")))
            key = ast.program_id or Path(ast.file_path).stem
            asts[key] = ast

    rules_map: dict[str, RulesOutput] = {}
    for rules_rel in manifest.artifacts.rules:
        rules_path = run_dir / rules_rel
        if rules_path.exists():
            ro = RulesOutput(**json.loads(rules_path.read_text(encoding="utf-8")))
            key = ro.program_id or Path(ro.file_path).stem
            rules_map[key] = ro

    explanations: dict[str, ExplanationOutput] = {}
    for doc_rel in manifest.artifacts.docs:
        if doc_rel.endswith("_explanation.json"):
            doc_path = run_dir / doc_rel
            if doc_path.exists():
                eo = ExplanationOutput(**json.loads(doc_path.read_text(encoding="utf-8")))
                key = eo.program_id or Path(eo.file_path).stem
                explanations[key] = eo

    # Generate per-program docs
    program_docs: list[ProgramDocumentation] = []
    generated_paths: list[Path] = []

    for key, ast in sorted(asts.items()):
        doc = generate_program_doc(
            ast=ast,
            rules=rules_map.get(key),
            call_graph=call_graph,
            explanation=explanations.get(key),
        )
        program_docs.append(doc)

        doc_path = run_dir / "docs" / f"{_slugify(key)}_doc.md"
        write_text_artifact(doc_path, doc.markdown)
        generated_paths.append(doc_path)

    # Generate project report
    report = generate_project_report(manifest, program_docs, call_graph)
    report_path = run_dir / "docs" / "project_report.md"
    write_text_artifact(report_path, report)
    generated_paths.append(report_path)

    return generated_paths


def _slugify(value: str) -> str:
    chars = [c.lower() if c.isalnum() else "_" for c in value.strip()]
    collapsed = "".join(chars)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed.strip("_") or "unknown"
