"""Benchmark script for cobol-intel parse performance and token savings.

Usage:
    python tools/benchmark.py [--samples-dir samples] [--output benchmark_results.json]
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cobol_intel.llm.context_builder import build_program_prompt
from cobol_intel.service.pipeline import (
    analyze_path,
    discover_cobol_files,
    to_ast_output,
)


@dataclass
class BenchmarkResult:
    file_path: str
    parse_success: bool
    parse_time_ms: float
    raw_chars: int
    prompt_chars: int
    token_savings_pct: float
    rules_count: int
    paragraphs_count: int
    data_items_count: int


def run_benchmark(
    samples_dir: Path,
    copybook_dirs: list[Path] | None = None,
) -> list[BenchmarkResult]:
    """Run benchmarks on all COBOL files in the samples directory."""
    results: list[BenchmarkResult] = []

    cobol_files = discover_cobol_files(samples_dir)
    if not cobol_files:
        print(f"No COBOL files found in {samples_dir}")
        return results

    output_dir = Path("benchmark_artifacts")

    run_result = analyze_path(
        path=samples_dir,
        output_dir=str(output_dir),
        copybook_dirs=[str(d) for d in (copybook_dirs or [])],
    )

    parse_map = {Path(r.file_path).name: r for r in run_result.parse_results}
    rules_map = {(ro.program_id or Path(ro.file_path).stem): ro for ro in run_result.rules_outputs}

    for cobol_file in cobol_files:
        raw_source = cobol_file.read_text(encoding="utf-8")
        raw_chars = len(raw_source)
        parse_result = parse_map.get(cobol_file.name)

        if parse_result and parse_result.success:
            file_start = time.perf_counter()
            ast_output = to_ast_output(parse_result, file_path=str(cobol_file))
            file_time_ms = (time.perf_counter() - file_start) * 1000

            rules_output = rules_map.get(parse_result.program_id or cobol_file.stem)
            prompt = build_program_prompt(ast_output, rules=rules_output)
            prompt_chars = len(prompt)
            savings = ((raw_chars - prompt_chars) / raw_chars * 100) if raw_chars > 0 else 0.0

            results.append(BenchmarkResult(
                file_path=str(cobol_file),
                parse_success=True,
                parse_time_ms=round(file_time_ms, 2),
                raw_chars=raw_chars,
                prompt_chars=prompt_chars,
                token_savings_pct=round(savings, 1),
                rules_count=len(rules_output.rules) if rules_output else 0,
                paragraphs_count=len(ast_output.paragraphs),
                data_items_count=len(ast_output.data_items),
            ))
        else:
            results.append(BenchmarkResult(
                file_path=str(cobol_file),
                parse_success=False,
                parse_time_ms=0.0,
                raw_chars=raw_chars,
                prompt_chars=0,
                token_savings_pct=0.0,
                rules_count=0,
                paragraphs_count=0,
                data_items_count=0,
            ))

    # Cleanup benchmark artifacts
    import shutil
    shutil.rmtree(output_dir, ignore_errors=True)

    return results


def format_markdown_table(results: list[BenchmarkResult]) -> str:
    """Render benchmark results as a Markdown table."""
    lines = [
        "# Benchmark Results",
        "",
        (
            "| File | Parse | Time (ms) | Raw Chars | Prompt Chars | Savings % "
            "| Rules | Paragraphs | Data Items |"
        ),
        "|------|-------|-----------|-----------|-------------|-----------|-------|------------|------------|",
    ]
    for r in results:
        status = "pass" if r.parse_success else "FAIL"
        name = Path(r.file_path).name
        lines.append(
            f"| {name} | {status} | {r.parse_time_ms} | {r.raw_chars} | "
            f"{r.prompt_chars} | {r.token_savings_pct}% | {r.rules_count} | "
            f"{r.paragraphs_count} | {r.data_items_count} |"
        )

    success_count = sum(1 for r in results if r.parse_success)
    total = len(results)
    lines.extend([
        "",
        (
            f"**Parse success rate**: {success_count}/{total} "
            f"({success_count/total*100:.0f}%)"
        ) if total else "",
    ])
    return "\n".join(lines)


@dataclass
class PromptComparisonResult:
    """Result of comparing raw source prompts vs structured pipeline prompts."""

    file_path: str
    program_id: str
    strategy: str
    mode: str
    prompt_chars: int
    response_chars: int
    input_tokens: int
    output_tokens: int
    has_traceability: bool
    has_rules_reference: bool
    has_structured_sections: bool


def run_prompt_comparison(
    samples_dir: Path,
    copybook_dirs: list[Path] | None = None,
    max_programs: int = 3,
) -> list[PromptComparisonResult]:
    """Compare raw source prompts vs structured pipeline prompts.

    This is a prompt-structure benchmark, not a live model-quality benchmark.
    It measures how much context and structure the pipeline adds before any
    backend inference happens.
    """
    from cobol_intel.analysis.rules_extractor import extract_rules
    from cobol_intel.contracts.explanation_output import ExplanationMode
    from cobol_intel.llm.context_builder import build_program_prompt, build_system_prompt
    from cobol_intel.parsers.antlr_parser import ANTLR4Parser
    from cobol_intel.parsers.preprocessor import COBOLPreprocessor

    results: list[PromptComparisonResult] = []

    cobol_files = discover_cobol_files(samples_dir)[:max_programs]
    parser = ANTLR4Parser()
    preprocessor = COBOLPreprocessor(
        copybook_dirs=[str(d) for d in (copybook_dirs or [])],
    )

    for cobol_file in cobol_files:
        source = cobol_file.read_text(encoding="utf-8")
        preprocessed = preprocessor.preprocess(source, file_path=str(cobol_file))
        parsed = parser.parse(preprocessed.text, file_path=str(cobol_file))

        if not parsed.success:
            continue

        ast_out = to_ast_output(parsed, file_path=str(cobol_file))
        rules = extract_rules(parsed, file_path=str(cobol_file))
        program_id = ast_out.program_id or cobol_file.stem

        for mode in ExplanationMode:
            # Raw approach: just send source code
            raw_prompt = source
            raw_chars = len(raw_prompt)

            # Pipeline approach: structured artifacts
            pipeline_prompt = build_program_prompt(ast_out, rules=rules)
            system_prompt = build_system_prompt(mode)
            pipeline_chars = len(pipeline_prompt) + len(system_prompt)

            # Measure quality indicators
            results.append(PromptComparisonResult(
                file_path=str(cobol_file),
                program_id=program_id,
                strategy="raw_source",
                mode=mode.value,
                prompt_chars=raw_chars,
                response_chars=0,
                input_tokens=raw_chars // 4,
                output_tokens=0,
                has_traceability=False,
                has_rules_reference=False,
                has_structured_sections=False,
            ))

            results.append(PromptComparisonResult(
                file_path=str(cobol_file),
                program_id=program_id,
                strategy="structured_pipeline",
                mode=mode.value,
                prompt_chars=pipeline_chars,
                response_chars=0,
                input_tokens=pipeline_chars // 4,
                output_tokens=0,
                has_traceability="## Paragraphs" in pipeline_prompt,
                has_rules_reference="## Extracted Business Rules" in pipeline_prompt,
                has_structured_sections=(
                    "## Data Items" in pipeline_prompt
                    and "## Paragraphs" in pipeline_prompt
                ),
            ))

    return results


# Backward-compatible alias for earlier internal drafts.
run_backend_comparison = run_prompt_comparison


def format_comparison_table(results: list[PromptComparisonResult]) -> str:
    """Render prompt strategy comparison as a Markdown table."""
    lines = [
        "# Prompt Strategy Comparison",
        "",
        "| Program | Strategy | Mode | Prompt Chars | ~Tokens | Traceable | Rules | Structured |",
        "|---------|---------|------|-------------|---------|-----------|-------|------------|",
    ]
    for r in results:
        lines.append(
            f"| {r.program_id} | {r.strategy} | {r.mode} | "
            f"{r.prompt_chars:,} | ~{r.input_tokens:,} | "
            f"{'yes' if r.has_traceability else 'no'} | "
            f"{'yes' if r.has_rules_reference else 'no'} | "
            f"{'yes' if r.has_structured_sections else 'no'} |"
        )

    # Summary
    raw = [r for r in results if r.strategy == "raw_source"]
    pipeline = [r for r in results if r.strategy == "structured_pipeline"]
    if raw and pipeline:
        avg_raw = sum(r.prompt_chars for r in raw) / len(raw)
        avg_pipe = sum(r.prompt_chars for r in pipeline) / len(pipeline)
        lines.extend([
            "",
            f"**Avg raw prompt**: {avg_raw:,.0f} chars",
            f"**Avg pipeline prompt**: {avg_pipe:,.0f} chars",
            (
                f"**Pipeline structured**: "
                f"{sum(1 for r in pipeline if r.has_structured_sections)}/{len(pipeline)}"
            ),
            (
                f"**Pipeline with rules**: "
                f"{sum(1 for r in pipeline if r.has_rules_reference)}/{len(pipeline)}"
            ),
        ])

    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark cobol-intel")
    parser.add_argument("--samples-dir", default="samples", help="COBOL samples directory")
    parser.add_argument("--copybook-dir", default="copybooks", help="Copybook directory")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON path")
    parser.add_argument(
        "--compare", action="store_true",
        help="Run raw vs structured-pipeline prompt comparison",
    )
    parser.add_argument(
        "--max-programs", type=int, default=5,
        help="Max programs for prompt comparison",
    )
    args = parser.parse_args()

    samples = Path(args.samples_dir)
    copybook_dirs = [Path(args.copybook_dir)] if Path(args.copybook_dir).exists() else []

    print(f"Running benchmark on {samples}...")
    results = run_benchmark(samples, copybook_dirs)

    # Write JSON
    output_path = Path(args.output)
    output_path.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    print(f"JSON results: {output_path}")

    # Write Markdown
    md_path = output_path.with_suffix(".md")
    md_path.write_text(format_markdown_table(results), encoding="utf-8")
    print(f"Markdown results: {md_path}")

    # Summary
    success = sum(1 for r in results if r.parse_success)
    print(f"\nParse success: {success}/{len(results)}")
    if results:
        avg_savings = sum(r.token_savings_pct for r in results if r.parse_success) / max(success, 1)
        print(f"Avg token savings: {avg_savings:.1f}%")

    # Prompt strategy comparison
    if args.compare:
        print(
            f"\nRunning prompt strategy comparison "
            f"(max {args.max_programs} programs)..."
        )
        comparison = run_prompt_comparison(
            samples, copybook_dirs, max_programs=args.max_programs,
        )
        comp_path = output_path.with_stem(output_path.stem + "_comparison")
        comp_path.write_text(
            json.dumps([asdict(r) for r in comparison], indent=2),
            encoding="utf-8",
        )
        comp_md = comp_path.with_suffix(".md")
        comp_md.write_text(format_comparison_table(comparison), encoding="utf-8")
        print(f"Comparison results: {comp_md}")

        raw = [r for r in comparison if r.strategy == "raw_source"]
        pipeline = [
            r for r in comparison if r.strategy == "structured_pipeline"
        ]
        print(
            f"  Raw prompts: {len(raw)}, "
            f"Structured pipeline prompts: {len(pipeline)}"
        )
        structured = sum(1 for r in pipeline if r.has_structured_sections)
        print(f"  Pipeline structured: {structured}/{len(pipeline)}")


if __name__ == "__main__":
    main()
