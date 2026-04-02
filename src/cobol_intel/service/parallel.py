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

# Bounded concurrency per backend. Local/self-hosted backends stay conservative.
_DEFAULT_WORKERS: dict[str, int] = {
    "claude": 4,
    "openai": 8,
    "ollama": 1,
    "local": 1,
}


@dataclass(frozen=True)
class ExplainJob:
    """One explain task with its own prompt transform policy."""

    index: int
    ast: ASTOutput
    rules: RulesOutput | None = None
    prompt_transform: Callable[[str], str] | None = None


@dataclass
class ParallelResult:
    """Result of a single parallel explanation attempt."""

    index: int
    explanation: ExplanationOutput | None = None
    error: Exception | None = None


def parallel_explain(
    jobs: list[ExplainJob],
    backend: LLMBackend,
    call_graph: CallGraphOutput | None = None,
    mode: ExplanationMode = ExplanationMode.TECHNICAL,
    max_workers: int | None = None,
) -> list[ParallelResult]:
    """Explain multiple programs in parallel with bounded concurrency."""
    if not jobs:
        return []

    workers = max_workers or _DEFAULT_WORKERS.get(backend.name, 4)
    results: list[ParallelResult] = [ParallelResult(index=job.index) for job in jobs]

    def _explain_one(job: ExplainJob) -> ParallelResult:
        try:
            worker_backend = backend.clone()
            explanation = explain_program(
                backend=worker_backend,
                ast=job.ast,
                rules=job.rules,
                call_graph=call_graph,
                mode=mode,
                prompt_transform=job.prompt_transform,
            )
            return ParallelResult(index=job.index, explanation=explanation)
        except Exception as exc:
            return ParallelResult(index=job.index, error=exc)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_explain_one, job): position
            for position, job in enumerate(jobs)
        }
        for future in as_completed(futures):
            result = future.result()
            results[futures[future]] = result

    return results
