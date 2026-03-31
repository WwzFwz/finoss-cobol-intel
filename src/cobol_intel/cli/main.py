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
