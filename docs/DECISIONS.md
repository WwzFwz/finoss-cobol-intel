# Architecture Decision Records (ADR)

Every important technical decision is documented here along with its rationale.
This is important for large projects so that the reasoning behind each choice is not forgotten.

Format for each entry:

- **Status**: Proposed / Accepted / Deprecated
- **Context**: The situation that necessitated this decision
- **Decision**: What was decided
- **Consequences**: Positive and negative impacts

---

## ADR-001: Python as the Primary Language

**Status**: Accepted

**Context**: A language needed to be chosen for building the entire pipeline.

**Decision**: Python 3.11+

**Consequences**:

- (+) The most complete ecosystem for LLM integration
- (+) `lark`, `antlr4-python3-runtime`, and data tooling are easy to use
- (+) Familiar to the data science / ML community
- (+) Easy to package and distribute
- (-) Slower than Go/Rust for intensive parsing
- (-) The GIL can become a bottleneck for certain parallelism scenarios

---

## ADR-002: Static Analysis Before LLM

**Status**: Accepted

**Context**: Technically, it is possible to send COBOL directly to an LLM and request an explanation.

**Decision**: Always run the static analysis pipeline first, then let the LLM receive
structured output.

**Consequences**:

- (+) The LLM receives cleaner input
- (+) Higher accuracy in explanations and rule extraction
- (+) Saves tokens by not sending the entire raw COBOL
- (+) The pipeline remains useful even when the LLM backend is unavailable
- (-) More complex architecture
- (-) The parser must be robust enough for various COBOL dialects

---

## ADR-003: Pluggable LLM Backend

**Status**: Accepted

**Context**: Enterprise users often cannot send source code to the cloud,
while individual developers want a quick setup.

**Decision**: Use a pluggable LLM backend abstraction.

Target implementations:

- OpenAI API
- Claude API
- Ollama
- Local model backend

**Consequences**:

- (+) Banks can use a fully on-premise setup with a local model
- (+) Developers can use an API for rapid iteration
- (+) Fine-tuned models can be added later
- (-) Multiple backend implementations need to be maintained
- (-) Testing becomes more complex

---

## ADR-004: CLI-First, GUI Later

**Status**: Accepted

**Context**: A web UI is more appealing for demos, but building it too early
risks driving an architecture that is not yet mature.

**Decision**: Focus on CLI and artifact output first. The GUI comes later
after the service layer and output contract are stable.

**Consequences**:

- (+) Faster value delivery for developers
- (+) Easier to integrate into scripts and CI/CD
- (+) Easier to test
- (+) The GUI will have a more stable foundation later
- (-) Early demos are less visual for a non-technical audience
- Mitigation: HTML reports and Mermaid diagrams can be used for early demos

---

## ADR-005: Primary Output Formats

**Status**: Accepted

**Context**: An output format is needed that serves various use cases.

**Decision**:

- **JSON** for programmatic integration and regression testing
- **Markdown** for documentation that can be rendered on GitHub or a wiki
- **HTML** for reports targeting non-technical stakeholders
- **Mermaid** for diagrams that can be embedded in Markdown

**Consequences**:

- (+) Flexible for many needs
- (+) JSON serves as the base contract across interfaces
- (+) Markdown can be pushed directly to a repo as docs
- (-) Generators are needed for multiple output formats

---

## ADR-006: Default Parser — ANTLR4

**Status**: Accepted (2026-03-31)

**Context**: The parser is the project's foundation, but choosing a parser based
solely on library preference is too risky. Phase 0 built a PoC using `lark`
(Earley) and `ANTLR4` on 5 real COBOL samples (fixed-format, free-format,
COPY, COMP-3, REDEFINES, OCCURS, CALL, EVALUATE, PERFORM VARYING, array access).

Both parsers successfully parsed all 5 samples — 32/32 tests for lark, 27/27 tests for ANTLR4.

**Decision**: **ANTLR4 as the default parser.** Lark remains available as a
fallback and for quick prototyping.

Key reasons:

1. Keyword/identifier priority is resolved naturally by lexer rule
   ordering — no need for priority annotation workarounds as in lark
2. A community COBOL85 grammar is available at `antlr/grammars-v4` as an upgrade path
3. The strongly-typed visitor pattern is more maintainable for large projects
4. The tooling and debugging ecosystem is more mature

Mitigation for the Java dependency risk:

- Generated Python files are committed to the repo
- Contributors only need Java when modifying the grammar
- End users do not need Java at all

Full evaluation: `docs/PARSER_EVALUATION.md`

**Consequences**:

- (+) Parser decision is evidence-based from a real PoC, not guesswork
- (+) Natural keyword priority without manual annotations
- (+) Community COBOL85 grammar available for scaling to real dialects
- (+) Strongly-typed context objects and visitor pattern
- (+) Lark remains available as a fallback
- (-) Java is required to regenerate the parser when the grammar changes
- (-) Generated code (~3000 lines) must be committed to the repo

---

## ADR-007: Versioned Contracts for All JSON Artifacts

**Status**: Accepted

**Context**: Without stable output contracts, the CLI, API, GUI, and external
integrations will easily break when the JSON shape changes.

**Decision**: All JSON artifacts must be defined in `contracts/` and must
include a `schema_version`.

Minimum artifacts for MVP:

- `manifest.json`
- AST output
- dependency graph output
- business rules output

**Consequences**:

- (+) Safer integrations
- (+) Contract tests can be written from the start
- (+) The API and GUI will share a common language later
- (-) Output changes become more disciplined and slightly slower

---

## ADR-008: File-System Artifact Store Before Database Persistence

**Status**: Accepted

**Context**: The project needs a clean model for runs and artifacts, but full
enterprise persistence is premature for the MVP.

**Decision**: Store analysis results in a stable artifact directory on the
filesystem. Do not build full database persistence in the early phase.

Example layout:

```text
artifacts/<project_slug>/<run_id>/
```

**Consequences**:

- (+) Simple for the MVP
- (+) Easy to inspect manually
- (+) Can be mapped to object storage or a DB later
- (-) Not yet optimal for multi-user and complex queries

---

## ADR-009: Package Boundaries Must Be Locked Before Coding

**Status**: Accepted

**Context**: Without clear boundaries, the CLI, parser, formatter, and LLM layer
will easily become coupled and difficult to refactor when an API or GUI is added.

**Decision**: Lock the following package layout from the start:

```text
src/cobol_intel/
  core/
  contracts/
  parsers/
  analysis/
  llm/
  outputs/
  service/
  cli/
```

Rules:

- `cli` does not hold business logic
- `analysis` does not depend on the LLM backend
- `contracts` serves as the shared language across layers
- new interfaces are added later through `service`

**Consequences**:

- (+) Future refactoring is cheaper
- (+) A GUI and API are easier to add later
- (+) Testing can be focused per layer
- (-) Boundary discipline is required from the start

---

## ADR-010: Testing Strategy Must Be Based on Corpus, Contract, and Regression

**Status**: Accepted

**Context**: Writing "there will be benchmarks and a test suite" is too vague for
a parser-heavy project like this.

**Decision**: Testing is divided into four layers:

1. corpus tests for parser and dialect coverage
2. contract tests for JSON schema
3. regression tests for expected artifacts
4. evaluation tests for comparing raw LLM vs. the preprocessing pipeline

**Consequences**:

- (+) Parser regression risks are detected faster
- (+) Output contracts remain stable
- (+) The LLM is proven to be an enhancer, not the sole foundation
- (-) Dataset effort and fixture maintenance are required

---

## ADR-011: API Deferred Until the Service Layer and Contracts Are Stable

**Status**: Accepted

**Context**: There is a need for integration with other systems, but building an API
too early could result in endpoints that become obsolete as soon as contracts change.

**Decision**: The API is not a priority in the early phase. Add a read-only API
prototype after the service layer and artifact contracts are stable.

**Consequences**:

- (+) The backend is not locked in too early by API design
- (+) Contracts are more mature when the API is introduced
- (+) The GUI can later be built on top of a healthier interface
- (-) HTTP-based integration is not available in the earliest MVP

---

## ADR-013: Error Handling Strategy — Partial Artifacts with Warnings

**Status**: Accepted

**Context**: COBOL codebases in real banks are never 100% clean. There are always
files with non-standard dialects, missing COPYBOOKs, or syntax edge cases
that the parser does not handle. There is no explicit decision yet on what
happens when the pipeline fails on some files.

Without this decision, implementers will make choices unconsciously and the
results will be inconsistent across modules.

**Decision**: The pipeline uses a **partial artifact with warnings** strategy,
not fail-fast.

Rules:

- If a single file fails to parse, that file is recorded in the `errors` section
  of `manifest.json`, and the pipeline continues to the next file.
- Successfully produced artifacts are still written to the filesystem.
- `manifest.json` receives a status of `partially_completed` if there are errors,
  not `completed`.
- If **all** files fail, the status becomes `failed`.
- Every error must include: file path, the module that failed, the error message,
  and if possible — the problematic line.

Example manifest with partial failure:

```json
{
  "schema_version": "1.0",
  "run_id": "run_20260331_001",
  "status": "partially_completed",
  "artifacts": {
    "ast": ["ast/CALCINT.json", "ast/PAYREC.json"]
  },
  "warnings": [
    "COPYBOOK 'CUSTMAST' not found, fields from this COPYBOOK were not resolved"
  ],
  "errors": [
    {
      "file": "LEGACY01.cbl",
      "module": "parser",
      "message": "Unexpected token at line 342: EXEC CICS — CICS dialect is not yet supported",
      "line": 342
    }
  ]
}
```

**Fail-fast only applies** to conditions that indicate an incorrect setup,
not problematic COBOL content. Examples: the input directory does not exist, the
LLM backend cannot be reached and LLM mode is required to be enabled.

**Consequences**:

- (+) The tool remains useful even when some files cannot be processed
- (+) Users know exactly which files are problematic and why
- (+) Partial artifacts can still be used for the files that succeeded
- (+) Consistent across modules — all follow the same rules
- (-) Implementation is more complex than simply raising an exception
- (-) Users must always check `manifest.json` and cannot assume a run equals success

---

## ADR-012: Enterprise Auth and RBAC Are Not in MVP Scope

**Status**: Accepted

**Context**: Auth, RBAC, and platform auditing are important for enterprise use,
but do not need to be built during the open-source MVP phase.

**Decision**: These features are deferred. The architecture only needs to ensure
that adding them later is not blocked.

**Consequences**:

- (+) Team focus remains on the parser, contracts, and core pipeline
- (+) The MVP is completed faster
- (-) Not yet ready to serve as a multi-user enterprise platform

---

## ADR-014: Run ID Format — Timestamp + Random Suffix

**Status**: Accepted (2026-03-31)

**Context**: The artifact directory layout uses `run_id` as the folder name
(`artifacts/<project>/<run_id>/`). The format has not been decided — the main
options are UUID v4 or timestamp-based.

**Decision**: Format `run_YYYYMMDD_HHMMSS_XXXX` where:

- Timestamp is in UTC
- `XXXX` is a 4-char hex random suffix for uniqueness within the same second

Example: `run_20260331_143052_a7f3`

**Consequences**:

- (+) Human-readable — easy to inspect in the filesystem and logs
- (+) Naturally sortable (ls, sort)
- (+) Unique enough for a single-user CLI tool
- (-) Not suitable for distributed multi-node systems (but that is not in MVP scope)
- (-) Not as short as UUID v4 for embedding in URLs later

Implementation: `src/cobol_intel/contracts/run_id.py`
