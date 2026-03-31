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
    AnalysisRunResult,
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

    start = time.perf_counter()
    run_result = analyze_path(
        path=samples_dir,
        output_dir=str(output_dir),
        copybook_dirs=[str(d) for d in (copybook_dirs or [])],
    )
    total_time_ms = (time.perf_counter() - start) * 1000

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
        "| File | Parse | Time (ms) | Raw Chars | Prompt Chars | Savings % | Rules | Paragraphs | Data Items |",
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
        f"**Parse success rate**: {success_count}/{total} ({success_count/total*100:.0f}%)" if total else "",
    ])
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark cobol-intel")
    parser.add_argument("--samples-dir", default="samples", help="COBOL samples directory")
    parser.add_argument("--copybook-dir", default="copybooks", help="Copybook directory")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON path")
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


if __name__ == "__main__":
    main()
