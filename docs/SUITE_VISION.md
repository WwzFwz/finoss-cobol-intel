# Suite Vision

This document describes the long-term direction of the project as a foundation
for a finance open-source suite, without expanding the current MVP scope.

The purpose of this document is not to add new features now, but to ensure that
technical decisions in the first module do not inadvertently lock the architecture
to COBOL-only use cases.

---

## Long-Term Direction

The long-term target is to build a collection of open-source modules for
finance needs that share a similar workflow pattern:

- accept reasonably structured input
- perform programmatic and/or LLM-assisted analysis
- produce artifacts that can be validated, traced, and integrated

The first module is `cobol-intel`.

Current working names:

- public repo: `cobol-intel`
- command line: `cobol-intel`
- Python package: `cobol_intel`

This means that even though there is a long-term suite vision, the published
project identity stays consistent as `cobol-intel`.

If the architecture proves sound in this module, the same pattern can be reused
for other modules such as:

- `regtech`
- `doc-intel`
- `aml-assist`
- `reconcile`

This list is still illustrative, not a roadmap commitment.

---

## Shared Layer Agreed Upon Now

For the current stage, the shared layer is deliberately limited to avoid
over-designing. Only the following five things may be considered reusable
across modules:

1. Artifact metadata and manifest pattern
2. Run lifecycle and execution status
3. Source reference model
4. LLM backend abstraction
5. Output formatter conventions

Brief explanation:

- **Artifact metadata and manifest pattern**
  All future modules should produce output with a consistent manifest pattern,
  including `schema_version`, `run_id`, status, artifact list, warnings, and errors.

- **Run lifecycle and execution status**
  The basic lifecycle such as `queued -> running -> completed/failed` should be
  consistent across all modules.

- **Source reference model**
  All findings or explanations should be able to point back to their source,
  whether it is a COBOL file, document, regulatory rule, or transaction dataset.

- **LLM backend abstraction**
  Model integration must remain pluggable and must not change the core pipeline.

- **Output formatter conventions**
  Formats like JSON, Markdown, HTML, and Mermaid should follow a uniform pattern
  across modules.

---

## Not Yet Decided

The following items are deliberately left undecided for now:

- final suite name
- final suite namespace above `cobol-intel`
- final suite-level monorepo layout
- whether shared code will be separated into a dedicated package
- shared finance domain types like `Money`, `DateRange`, and similar
- the second module after `cobol-intel`

Reasons for deferral:

- shared layer needs will become clearer after one module is actually running
- locking suite abstractions too early can produce a design that looks clean on paper
  but is not used in practice

---

## Decision Timing

Recommended decision timing:

- **Now**
  Agree that this project should remain `suite-friendly`, but stay focused
  on `cobol-intel` as the first module.

- **After `cobol-intel` completes Phase 0**
  Review whether contracts, artifact model, and service boundaries are sufficiently
  reusable or still too COBOL-specific.

- **After `cobol-intel` completes Phase 1**
  Then decide:
  - suite name
  - long-term package namespace
  - repo strategy: stay single repo or convert to formal monorepo
  - which shared layers are actually promoted to reusable packages

---

## Explicit Constraints

These constraints apply so that the suite vision does not derail MVP focus:

- Do not create new modules before `cobol-intel` completes at least Phase 1.
- Do not add new shared layer abstractions without at least two real use cases.
- Do not sacrifice `cobol-intel` architecture clarity just for suite hypotheses.
- Do not build a large platform before the first engine is proven useful.

---

## Working Principle

Working principle for the first few months:

- build `cobol-intel` as if it is the first module of a suite
- evaluate shared concerns with discipline
- generalize only what is genuinely proven reusable

With this approach, the project stays focused as an MVP that can be completed, while
not closing the door to growing into a finance open-source suite in the future.
