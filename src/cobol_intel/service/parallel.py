"""Bounded parallel LLM explanation processing."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from cobol_intel.contracts.ast_output import ASTOutput
from cobol_intel.contracts.explanation_output import ExplanationMode, ExplanationOutput
from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.rules_output import RulesOutput
from cobol_intel.llm.backend import LLMBackend
from cobol_intel.llm.explainer import explain_program

# Bounded concurrency per backend — respects rate limits
_DEFAULT_WORKERS: dict[str, int] = {
    "claude": 4,
    "openai": 8,
    "ollama": 1,
}


@dataclass
class ParallelResult:
    """Result of a single parallel explanation attempt."""

    index: int
    explanation: ExplanationOutput | None = None
    error: Exception | None = None


def parallel_explain(
    programs: list[tuple[ASTOutput, RulesOutput | None]],
    backend: LLMBackend,
    call_graph: CallGraphOutput | None = None,
    mode: ExplanationMode = ExplanationMode.TECHNICAL,
    max_workers: int | None = None,
    prompt_transform: Callable[[str], str] | None = None,
) -> list[ParallelResult]:
    """Explain multiple programs in parallel with bounded concurrency.

    Args:
        programs: List of (ast, optional rules) tuples to explain.
        backend: The LLM backend to use.
        call_graph: Optional call graph for cross-program context.
        mode: Explanation mode.
        max_workers: Override concurrency limit. Defaults per-backend.
        prompt_transform: Optional prompt transformation (e.g. redaction).

    Returns:
        List of ParallelResult in the same order as input programs.
    """
    if not programs:
        return []

    workers = max_workers or _DEFAULT_WORKERS.get(backend.name, 4)
    results: list[ParallelResult] = [ParallelResult(index=i) for i in range(len(programs))]

    def _explain_one(index: int, ast: ASTOutput, rules: RulesOutput | None) -> ParallelResult:
        try:
            explanation = explain_program(
                backend=backend,
                ast=ast,
                rules=rules,
                call_graph=call_graph,
                mode=mode,
                prompt_transform=prompt_transform,
            )
            return ParallelResult(index=index, explanation=explanation)
        except Exception as exc:
            return ParallelResult(index=index, error=exc)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_explain_one, i, ast, rules): i
            for i, (ast, rules) in enumerate(programs)
        }
        for future in as_completed(futures):
            result = future.result()
            results[result.index] = result

    return results
