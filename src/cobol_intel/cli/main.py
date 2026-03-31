"""CLI entrypoint for cobol-intel."""

from __future__ import annotations

from pathlib import Path

import typer

from cobol_intel.service import analyze_path

app = typer.Typer(
    name="cobol-intel",
    help="Understand, document, and analyze legacy COBOL codebases.",
    no_args_is_help=True,
)

_BACKENDS = {"claude", "openai", "ollama", "none"}


@app.command()
def analyze(
    path: str = typer.Argument(..., help="Path to COBOL file or directory"),
    output_dir: str = typer.Option("artifacts", "--output", "-o", help="Output directory"),
    model: str = typer.Option("none", "--model", "-m", help="LLM backend: claude, openai, ollama, none"),
    mode: str = typer.Option("technical", "--mode", help="Explanation mode: technical, business, audit"),
    copybook_dir: list[str] = typer.Option(None, "--copybook-dir", help="Directory containing COPYBOOK files"),
    policy_config: str | None = typer.Option(None, "--policy-config", help="Optional JSON policy config path"),
    strict_policy: bool = typer.Option(False, "--strict-policy", help="Hard block policy violations during explain"),
    max_tokens_per_run: int | None = typer.Option(None, "--max-tokens-per-run", help="Optional token cap for one explain run"),
) -> None:
    """Analyze a COBOL program or directory and produce artifacts."""
    dirs = copybook_dir or _default_copybook_dirs(path)

    if model != "none":
        from cobol_intel.contracts.explanation_output import ExplanationMode
        from cobol_intel.service.explain import explain_path

        backend = _resolve_backend(model)
        result, explanations = explain_path(
            path=path, backend=backend,
            mode=ExplanationMode(mode), output_dir=output_dir,
            copybook_dirs=dirs,
            policy_config_path=policy_config,
            strict_policy=True if strict_policy else None,
            max_tokens_per_run=max_tokens_per_run,
        )
        typer.echo(f"[cobol-intel] analyze+explain: {path} via {model}")
        typer.echo(f"Programs explained: {len(explanations)}")
        total_tokens = sum(e.tokens_used for e in explanations)
        typer.echo(f"Total tokens: {total_tokens}")
    else:
        result = analyze_path(path=path, output_dir=output_dir, copybook_dirs=dirs)
        typer.echo(f"[cobol-intel] analyze: {path}")

    typer.echo(f"Run ID: {result.manifest.run_id}")
    typer.echo(f"Status: {result.manifest.status.value}")
    typer.echo(f"Artifacts: {result.run_dir}")


@app.command()
def explain(
    path: str = typer.Argument(..., help="Path to COBOL file or directory"),
    output_dir: str = typer.Option("artifacts", "--output", "-o", help="Output directory"),
    model: str = typer.Option("claude", "--model", "-m", help="LLM backend: claude, openai, ollama"),
    mode: str = typer.Option("technical", "--mode", help="Explanation mode: technical, business, audit"),
    copybook_dir: list[str] = typer.Option(None, "--copybook-dir", help="Directory containing COPYBOOK files"),
    policy_config: str | None = typer.Option(None, "--policy-config", help="Optional JSON policy config path"),
    strict_policy: bool = typer.Option(False, "--strict-policy", help="Hard block policy violations during explain"),
    max_tokens_per_run: int | None = typer.Option(None, "--max-tokens-per-run", help="Optional token cap for one explain run"),
) -> None:
    """Explain what a COBOL program does using an LLM backend."""
    from cobol_intel.contracts.explanation_output import ExplanationMode
    from cobol_intel.service.explain import explain_path

    backend = _resolve_backend(model)
    explanation_mode = ExplanationMode(mode)

    run_result, explanations = explain_path(
        path=path,
        backend=backend,
        mode=explanation_mode,
        output_dir=output_dir,
        copybook_dirs=copybook_dir or _default_copybook_dirs(path),
        policy_config_path=policy_config,
        strict_policy=True if strict_policy else None,
        max_tokens_per_run=max_tokens_per_run,
    )
    typer.echo(f"[cobol-intel] explain: {path} via {model} ({mode} mode)")
    typer.echo(f"Run ID: {run_result.manifest.run_id}")
    typer.echo(f"Programs explained: {len(explanations)}")
    total_tokens = sum(e.tokens_used for e in explanations)
    typer.echo(f"Total tokens used: {total_tokens}")
    typer.echo(f"Artifacts: {run_result.run_dir}")


@app.command()
def graph(
    path: str = typer.Argument(..., help="Path to COBOL directory"),
    output_dir: str = typer.Option("artifacts", "--output", "-o", help="Output directory"),
    copybook_dir: list[str] = typer.Option(None, "--copybook-dir", help="Directory containing COPYBOOK files"),
) -> None:
    """Build dependency and call graph for a COBOL codebase."""
    result = analyze_path(
        path=path,
        output_dir=output_dir,
        copybook_dirs=copybook_dir or _default_copybook_dirs(path),
    )
    typer.echo(f"[cobol-intel] graph: {path}")
    typer.echo(f"Graph artifacts written to: {result.run_dir / 'graphs'}")


@app.command()
def impact(
    run_dir: str = typer.Argument(..., help="Path to a completed run directory"),
    changed_program: list[str] = typer.Option(None, "--changed-program", "-p", help="Program ID that changed"),
    changed_field: list[str] = typer.Option(None, "--changed-field", "-f", help="Data field name that changed"),
    max_depth: int = typer.Option(3, "--max-depth", help="Max call graph traversal depth"),
) -> None:
    """Analyze change impact from a completed analysis run."""
    import json
    from cobol_intel.analysis.impact_analyzer import analyze_impact
    from cobol_intel.contracts.ast_output import ASTOutput
    from cobol_intel.contracts.graph_output import CallGraphOutput
    from cobol_intel.contracts.manifest import Manifest
    from cobol_intel.contracts.rules_output import RulesOutput

    run_path = Path(run_dir)
    manifest = Manifest(**json.loads((run_path / "manifest.json").read_text(encoding="utf-8")))

    call_graph = None
    for g in manifest.artifacts.graphs:
        if "call_graph.json" in g:
            call_graph = CallGraphOutput(**json.loads((run_path / g).read_text(encoding="utf-8")))

    asts: dict[str, ASTOutput] = {}
    for a in manifest.artifacts.ast:
        ast = ASTOutput(**json.loads((run_path / a).read_text(encoding="utf-8")))
        asts[ast.program_id or Path(ast.file_path).stem] = ast

    rules_map: dict[str, RulesOutput] = {}
    for r in manifest.artifacts.rules:
        ro = RulesOutput(**json.loads((run_path / r).read_text(encoding="utf-8")))
        rules_map[ro.program_id or Path(ro.file_path).stem] = ro

    report = analyze_impact(
        changed_programs=changed_program or [],
        changed_fields=changed_field or [],
        call_graph=call_graph or CallGraphOutput(),
        rules_by_program=rules_map,
        asts_by_program=asts,
        max_depth=max_depth,
    )
    typer.echo(f"[cobol-intel] impact: {report.total_impacted} program(s) affected")
    for entity in report.impacted_entities:
        typer.echo(f"  {entity.program_id} ({entity.impact_type.value}, depth={entity.distance}): {entity.reason}")


@app.command()
def docs(
    run_dir: str = typer.Argument(..., help="Path to a completed run directory"),
) -> None:
    """Generate documentation from a completed analysis run."""
    from cobol_intel.service.doc_service import generate_docs

    run_path = Path(run_dir)
    if not (run_path / "manifest.json").exists():
        typer.echo(f"Error: No manifest.json found in {run_dir}", err=True)
        raise typer.Exit(1)

    generated = generate_docs(run_path)
    typer.echo(f"[cobol-intel] docs: generated {len(generated)} file(s)")
    for path in generated:
        typer.echo(f"  {path}")


def _resolve_backend(model: str):
    """Resolve LLM backend from model name."""
    from cobol_intel.llm.backend import LLMBackend
    if model == "claude":
        from cobol_intel.llm.claude_backend import ClaudeBackend
        return ClaudeBackend()
    elif model == "openai":
        from cobol_intel.llm.openai_backend import OpenAIBackend
        return OpenAIBackend()
    elif model == "ollama":
        from cobol_intel.llm.ollama_backend import OllamaBackend
        return OllamaBackend()
    else:
        raise typer.BadParameter(f"Unknown model: {model}. Use: claude, openai, ollama")


def _default_copybook_dirs(path: str) -> list[str]:
    """Best-effort COPYBOOK directory detection for local workflows."""
    input_path = Path(path)
    candidates = [
        input_path.parent / "copybooks" if input_path.is_file() else input_path / "copybooks",
        Path.cwd() / "copybooks",
    ]
    return [str(candidate) for candidate in candidates if candidate.exists()]


if __name__ == "__main__":
    app()
