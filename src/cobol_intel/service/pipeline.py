"""Phase 1 analysis pipeline and artifact writer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cobol_intel import __version__
from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.analysis.rules_extractor import extract_rules
from cobol_intel.contracts.ast_output import ASTOutput, DataItemOut, ParagraphOut, StatementOut
from cobol_intel.contracts.governance import AuditEvent
from cobol_intel.contracts.manifest import ArtifactIndex, ErrorCode, Manifest, RunError, RunStatus
from cobol_intel.contracts.rules_output import RulesOutput
from cobol_intel.contracts.run_id import generate_run_id
from cobol_intel.outputs import (
    ensure_directory,
    render_rules_markdown,
    render_summary_markdown,
    write_json_artifact,
    write_text_artifact,
)
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.base import DataItemNode, ParagraphNode, ParseResult, StatementNode
from cobol_intel.parsers.preprocessor import COBOLPreprocessor
from cobol_intel.service.governance import default_actor, initialize_audit_log, append_audit_event

COBOL_SUFFIXES = {".cbl", ".cob", ".cobol"}


@dataclass
class AnalysisRunResult:
    """Convenience wrapper returned by the service layer."""

    manifest: Manifest
    run_dir: Path
    parse_results: list[ParseResult]
    rules_outputs: list[RulesOutput]


def analyze_path(
    path: str | Path,
    output_dir: str | Path = "artifacts",
    copybook_dirs: list[str | Path] | None = None,
) -> AnalysisRunResult:
    """Analyze a COBOL file or directory and write Phase 1 artifacts."""
    input_path = Path(path)
    discovered = discover_cobol_files(input_path)
    if not discovered:
        raise FileNotFoundError(f"No COBOL files found under: {input_path}")

    run_id = generate_run_id()
    project_name = slugify(input_path.stem if input_path.is_file() else input_path.name)
    run_dir = ensure_directory(Path(output_dir) / project_name / run_id)

    manifest = Manifest(
        tool_version=__version__,
        run_id=run_id,
        project_name=project_name,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        input_paths=[str(input_path)],
        artifacts=ArtifactIndex(),
    )
    audit_log_path = initialize_audit_log(manifest, run_dir)
    append_audit_event(
        audit_log_path,
        AuditEvent(
            event_type="analysis.run.started",
            run_id=run_id,
            actor=default_actor(),
            details={"input_paths": [str(input_path)]},
        ),
    )

    parser = ANTLR4Parser()
    preprocessor = COBOLPreprocessor(copybook_dirs=[str(Path(d)) for d in (copybook_dirs or [])])
    parse_results: list[ParseResult] = []

    for file_path in discovered:
        preprocessed = preprocessor.preprocess(
            file_path.read_text(encoding="utf-8"),
            file_path=str(file_path),
        )
        parsed = parser.parse(preprocessed.text, file_path=str(file_path))
        parsed.copybooks_used = sorted(set(parsed.copybooks_used) | set(preprocessed.copybooks_resolved))
        parsed.warnings.extend(preprocessed.warnings)
        parse_results.append(parsed)

        if parsed.errors:
            manifest.errors.extend(
                RunError(file=str(file_path), code=ErrorCode.PARSE_SYNTAX, module="parser", message=error)
                for error in parsed.errors
            )
        manifest.warnings.extend(preprocessed.warnings)
        manifest.warnings.extend(parsed.warnings)

    successful_results = [result for result in parse_results if result.success]

    rules_outputs = [
        extract_rules(result, file_path=result.file_path)
        for result in successful_results
    ]
    call_graph = build_call_graph(successful_results)

    ast_dir = ensure_directory(run_dir / "ast")
    graphs_dir = ensure_directory(run_dir / "graphs")
    rules_dir = ensure_directory(run_dir / "rules")
    docs_dir = ensure_directory(run_dir / "docs")

    for result in successful_results:
        ast_output = to_ast_output(result, file_path=result.file_path)
        artifact_name = _artifact_name(result.program_id, result.file_path)
        rel_path = Path("ast") / f"{artifact_name}.json"
        write_json_artifact(run_dir / rel_path, ast_output)
        manifest.artifacts.ast.append(rel_path.as_posix())

    for rules_output in rules_outputs:
        artifact_name = _artifact_name(rules_output.program_id, rules_output.file_path)
        rules_rel = Path("rules") / f"{artifact_name}.json"
        write_json_artifact(run_dir / rules_rel, rules_output)
        manifest.artifacts.rules.append(rules_rel.as_posix())

        md_rel = Path("docs") / f"{artifact_name}_rules.md"
        write_text_artifact(run_dir / md_rel, render_rules_markdown(rules_output))
        manifest.artifacts.docs.append(md_rel.as_posix())

    graph_json_rel = Path("graphs") / "call_graph.json"
    write_json_artifact(run_dir / graph_json_rel, call_graph)
    manifest.artifacts.graphs.append(graph_json_rel.as_posix())

    graph_mermaid_rel = Path("graphs") / "call_graph.mmd"
    write_text_artifact(run_dir / graph_mermaid_rel, call_graph.to_mermaid())
    manifest.artifacts.graphs.append(graph_mermaid_rel.as_posix())

    manifest.status = _final_status(parse_results)
    manifest.finished_at = datetime.now(timezone.utc)

    summary_rel = Path("docs") / "summary.md"
    write_text_artifact(run_dir / summary_rel, render_summary_markdown(manifest, rules_outputs, call_graph))
    manifest.artifacts.docs.append(summary_rel.as_posix())

    write_json_artifact(run_dir / "manifest.json", manifest)
    append_audit_event(
        audit_log_path,
        AuditEvent(
            event_type="analysis.run.completed",
            run_id=run_id,
            actor=default_actor(),
            status=manifest.status.value,
            details={
                "program_count": len(manifest.artifacts.ast),
                "warning_count": len(manifest.warnings),
                "error_count": len(manifest.errors),
            },
        ),
    )

    return AnalysisRunResult(
        manifest=manifest,
        run_dir=run_dir,
        parse_results=parse_results,
        rules_outputs=rules_outputs,
    )


def discover_cobol_files(path: Path) -> list[Path]:
    """Discover COBOL files under a file path or directory."""
    if path.is_file():
        return [path] if path.suffix.lower() in COBOL_SUFFIXES else []

    files = [
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in COBOL_SUFFIXES
    ]
    return sorted(files)


def to_ast_output(result: ParseResult, file_path: str = "") -> ASTOutput:
    """Convert parser dataclasses into the versioned AST output contract."""
    return ASTOutput(
        program_id=result.program_id,
        file_path=file_path,
        parser_name=result.parser_name,
        procedure_using=result.procedure_using,
        data_items=[_to_data_item(item) for item in result.data_items],
        paragraphs=[_to_paragraph(paragraph) for paragraph in result.paragraphs],
        copybooks_used=result.copybooks_used,
    )


def _to_data_item(node: DataItemNode) -> DataItemOut:
    return DataItemOut(
        level=node.level,
        name=node.name,
        pic=node.pic,
        usage=node.usage,
        value=node.value,
        redefines=node.redefines,
        occurs=node.occurs,
        is_condition=node.is_condition,
        condition_values=node.condition_values,
        children=[_to_data_item(child) for child in node.children],
        source=node.source,
    )


def _to_paragraph(node: ParagraphNode) -> ParagraphOut:
    return ParagraphOut(
        name=node.name,
        statements=[_to_statement(statement) for statement in node.statements],
        source=node.source,
    )


def _to_statement(node: StatementNode) -> StatementOut:
    return StatementOut(
        type=node.type,
        raw=node.raw,
        target=node.target,
        condition=node.condition,
        children=[_to_statement(child) for child in node.children],
        source=node.source,
    )


def _final_status(results: list[ParseResult]) -> RunStatus:
    if not results:
        return RunStatus.FAILED
    if all(result.success for result in results):
        return RunStatus.COMPLETED
    if any(result.success for result in results):
        return RunStatus.PARTIALLY_COMPLETED
    return RunStatus.FAILED


def _artifact_name(program_id: str | None, file_path: str) -> str:
    if program_id:
        return slugify(program_id)
    return slugify(Path(file_path).stem or "unknown")


def slugify(value: str) -> str:
    """Simple filesystem-safe slug."""
    chars = [
        char.lower() if char.isalnum() else "_"
        for char in value.strip()
    ]
    collapsed = "".join(chars)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed.strip("_") or "unknown"
