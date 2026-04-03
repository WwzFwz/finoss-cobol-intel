# COBOL Intelligence Platform - Project Plan

## Vision

An open-source platform that enables fintech companies and banks to understand,
document, and prepare for the migration of their legacy COBOL systems
using a combination of static analysis and LLM, capable of running entirely
on-premise without sending code to external servers.

---

## Problem Statement

Banks and fintech companies with legacy COBOL systems face three main problems:

1. **Knowledge loss** - COBOL developers are retiring, documentation is minimal, and system knowledge is being lost.
2. **Fear of change** - No one knows the impact of even the smallest change.
3. **Regulatory pressure** - Regulators demand system explanations, but banks struggle to respond quickly.

Existing solutions such as large enterprise tools or consultants are very expensive.
There is no open-source tool that truly focuses on understanding and documenting
COBOL with an approach that is safe for regulated environments.

---

## Core Principle

> An LLM is only as good as the input it receives.
> This project is the infrastructure layer that ensures that input is correct before
> the LLM touches it.

---

## MVP Guardrails

To keep this project executable and not over-engineered in the early phases:

- Stabilize the **contract output** before building many features.
- Validate the **parser strategy** with a small proof of concept, not assumptions.
- Separate **core logic** from CLI, output formatter, and LLM backend from the start.
- Use an extensible **filesystem artifact layout** before adding a database.
- Defer **auth, RBAC, multi-user persistence, and admin enterprise features**
  until there is a real need.

---

## Package Structure

The package structure must be locked before coding so that CLI, API, and GUI can
later use the same foundation.

```text
src/cobol_intel/
+-- core/         # domain models and orchestration free from UI
+-- contracts/    # Pydantic schemas, schema versioning, manifest
+-- parsers/      # COBOL parser, preprocessor, COPYBOOK resolver
+-- analysis/     # graph builder, rules extractor, impact analysis
+-- llm/          # backend adapters: OpenAI, Claude, Ollama, local
+-- outputs/      # markdown/json/html/mermaid generators
+-- service/      # pipeline service, run management, artifact writer
`-- cli/          # command-line entrypoints
```

Boundary rules:

- `core` and `contracts` must not import from `cli`.
- `analysis` and `parsers` must not depend on the LLM backend.
- `cli` only calls `service` and does not hold business logic.
- GUI or API must later become consumers of `service` and `contracts`,
  not access internals arbitrarily.

---

## Output Contracts And Artifact Layout

Before API or GUI integration is built, this project must have stable output
contracts.

### Contract Principles

- All JSON artifacts must have a `schema_version`.
- All runs must have a `run_id`, `created_at`, `status`, and `tool_version`.
- Output must be backward-conscious. Major shape changes must increment the schema version.
- Contracts are stored in `contracts/` and validated through automated tests.

### Job Lifecycle

Minimum lifecycle for all executions:

```text
queued -> running -> completed
queued -> running -> failed
```

These statuses are used first in CLI manifest and artifact metadata. Later,
the same statuses can be reused by API and GUI.

### Artifact Directory Layout

For MVP, full database persistence is not required. Instead, each
analysis run is written to the filesystem with a stable layout:

```text
artifacts/
`-- <project_slug>/
    `-- <run_id>/
        +-- manifest.json
        +-- ast/
        |   `-- <program>.json
        +-- graphs/
        |   +-- dependency_graph.json
        |   `-- dependency_graph.mmd
        +-- rules/
        |   `-- business_rules.json
        +-- docs/
        |   +-- summary.md
        |   `-- summary.html
        `-- logs/
            `-- pipeline.log
```

`manifest.json` must contain at minimum:

- `schema_version`
- `run_id`
- `project_name`
- `input_paths`
- `status`
- `started_at`
- `finished_at`
- `artifacts`
- `warnings`
- `errors`

This layout was deliberately chosen so that it can later be easily mapped to object storage or
a database without changing the logical artifact structure.

---

## Core Modules

### Module 1 - COBOL Parser And AST Builder

**Goal**: Understand COBOL structure programmatically, not through guesswork.

Input: `.cbl`, `.cob`, `.cobol` files
Output: Structured Abstract Syntax Tree (AST) in JSON

What must be handled:

- IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE DIVISION
- WORKING-STORAGE SECTION, FILE SECTION, LINKAGE SECTION
- COBOL data types: PIC, COMP, COMP-3, COMP-5
- OCCURS, REDEFINES, FILLER
- Fixed-format vs free-format COBOL

Important notes:

- The parser choice must not be locked based on opinion alone.
- Phase 0 must run a small PoC for `lark` and `ANTLR4` on real COBOL samples
  before a final decision is made.

---

### Module 2 - COPYBOOK And Dependency Resolver

**Goal**: Resolve all external dependencies before analysis.

Input: AST + COPYBOOK directory
Output: Fully resolved AST, inter-file dependency graph

What must be handled:

- `COPY` statement resolution
- `CALL` statement mapping for static calls
- Circular dependency detection
- Missing COPYBOOK warning

---

### Module 3 - Business Rules Extractor

**Goal**: Extract business conditions from the PROCEDURE DIVISION into a
human-readable format.

Input: resolved AST
Output: Decision table and rule list in JSON and Markdown format

Example output:

```text
Rule #12: Premium rate applies if:
  - Account type = SAVINGS
  - Balance > 10,000
  - Tenure >= 2 years
Source: CALCINT.cbl, line 247-263
```

---

### Module 4 - Dependency And Call Graph Builder

**Goal**: Complete map of relationships between programs.

Input: collection of COBOL files in a single project
Output: Visual graph in Mermaid/Graphviz and adjacency list JSON

What is visualized:

- `CALL` between programs
- `COPY` for shared data structures
- Shared files via `SELECT` and `ASSIGN`

---

### Module 5 - LLM Explanation Engine

**Goal**: Generate accurate natural language explanations from a clean AST.

Input: resolved AST + business rules + call graph, not raw COBOL
Output: Plain English explanations, technical documentation, and business summaries

Modes:

- `--mode technical` for developers
- `--mode business` for non-technical stakeholders
- `--mode audit` for compliance needs

Pluggable supported models:

- Claude API / OpenAI API for development and testing
- Ollama + local model for on-premise environments
- Fine-tuned COBOL model as a long-term target

MVP notes:

- LLM is not required for all commands.
- The static analysis pipeline must remain useful even when the LLM backend is unavailable.
- All LLM output must be traceable to the static analysis artifact that served as its source.

---

### Module 6 - Documentation Generator

**Goal**: Auto-generate complete documentation from the COBOL codebase.

Output per program:

- Function description
- Data dictionary for each field
- Input/output specification
- Discovered business rules
- Dependency list
- Flow diagram in Mermaid

Output format: Markdown, HTML, JSON

---

### Module 7 - Change Impact Analyzer

**Goal**: Answer the question "if I change X, what is affected?"

Input: field name, condition, or program name + full codebase graph
Output: List of affected programs, rules, and fields along with risk level

---

## System Architecture

```text
CLI
  |
  v
Service Layer
  |
  +-- Static Analysis Pipeline
  |     +-- Parser
  |     +-- Resolver
  |     +-- Graph Builder
  |     `-- Rules Extractor
  |
  +-- LLM Layer
  |     +-- OpenAI
  |     +-- Claude
  |     +-- Ollama
  |     `-- Local model
  |
  `-- Output Generator
        +-- JSON artifacts
        +-- Markdown docs
        +-- HTML report
        `-- Graph output
```

---

## Integration Strategy

This project is designed so that enterprise integration can be done incrementally without
forcing us to build a full platform from day one.

Integration principles:

- CLI is the **first client** of the service layer, not the center of business logic.
- The primary contract for early integration is **JSON artifact + manifest**, not a web dashboard.
- An API layer may be added after the contract output and service layer are stable.
- GUI is an optional consumer and must not dictate the design of the core pipeline.

### GUI Strategy

GUI may be built later, but:

- It is not a priority for Phase 0 or Phase 1
- It should remain in one repo until `contracts` and `service` are stable
- If the repo is ever split, GUI must consume versioned contracts,
  not import internal modules directly

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| COBOL Parser | `lark` or `antlr4-python3-runtime` |
| Graph | `networkx` + `graphviz` / Mermaid |
| LLM Interface | `anthropic`, `openai`, `ollama` |
| Contract Validation | `pydantic` |
| CLI | `click` or `typer` |
| Output | Markdown, JSON, HTML |
| Testing | `pytest` + COBOL sample corpus |
| Packaging | `pip` installable, Docker image |

---

## Development Phases

### Phase 0 - Foundation (Week 1-2)

- [x] Setup project structure and environment
- [x] Lock package structure: `core`, `contracts`, `parsers`, `analysis`,
      `llm`, `outputs`, `service`, `cli`
- [x] Define initial output schemas: `manifest`, `ast`, `dependency_graph`,
      `business_rules`
- [x] Determine versioning strategy for all JSON artifacts (`schema_version`)
- [x] Determine artifact directory layout for each analysis run
- [x] Collect COBOL sample datasets from Open Mainframe Project, IBM, Rosetta,
      and fixed-format samples
- [x] Create initial parser corpus: at least 3-4 realistic COBOL samples from different sources
- [x] Create PoC parser with `lark`
- [x] Create PoC parser with `ANTLR4` COBOL grammar
- [x] Compare PoC results and lock parser approach
- [x] Basic AST output for simple programs
- [x] First manifest run valid against schema

### Phase 1 - Static Analysis Core (Week 3-5)

- [x] Complete parser for main divisions and sections
- [x] Handle fixed-format preprocessing
- [x] COPYBOOK resolver
- [x] Circular dependency detection between COPYBOOKs
- [x] Call graph builder
- [x] Business rules extractor for `IF` and `EVALUATE` conditions
- [x] Basic dependency graph visualization
- [x] Consistent JSON artifact writer to artifact directory
- [x] Contract tests for all JSON output
- [x] Corpus test suite: at least 10 COBOL programs
- [x] Regression tests for sample corpus

### Phase 2 - LLM Integration (Week 6-8)

- [x] `service` orchestration to run the pipeline end-to-end
- [x] Context builder from AST to LLM-ready prompts
- [x] Smart chunking for large programs
- [x] Pluggable model interface
- [x] Explanation engine for technical mode
- [x] Explanation engine for business mode
- [x] Traceability: LLM output points to source artifact and program location

### Phase 3 - Output, Governance, And Integration (Week 9-10)

- [x] Audit/event log artifact (`logs/audit_events.jsonl`) for analysis and explain runs
- [x] Governance summary in `manifest.json` for sensitivity, deployment tier, and token usage
- [x] Approved model registry + preset helpers for LLM backend
- [x] Sensitivity classification helper for COBOL artifacts
- [x] Redaction helper for cloud prompts on sensitive workloads
- [x] Basic retry / timeout policy per backend
- [x] Token budget per explain run
- [x] Strict policy enforcement for sensitive workloads on cloud backends
- [x] Configurable policy registry via JSON config
- [x] Documentation generator for Markdown
- [x] Change impact analyzer
- [x] HTML report generator
- [x] Deep analysis: CFG builder, data flow, dead code detection, reference indexer
- [x] CLI polishing (--version, help text, command docs)
- [x] CHANGELOG.md and versioning (0.3.0)
- [x] Docker image hardened (multi-stage, non-root, health check)
- [x] Comprehensive README
- [x] Optional read-only API prototype to consume artifacts
- [ ] Cleaner output directory and artifact browsing
- [ ] Finalize layout to be ready for GUI consumption later

### Phase 4 - Fine-Tuning Infrastructure And Packaging (Week 11-12+)

- [x] Prompt comparison benchmark (`raw source` vs `structured pipeline`)
- [x] Fine-tuning dataset builder (Alpaca + ShareGPT format)
- [x] LoRA/PEFT fine-tuning script (CodeLlama-7B compatible)
- [x] Local fine-tuned model backend adapter
- [x] Optional extras for `.[local]` and `.[train]`
- [x] Deterministic default for offline local inference
- [x] PyPI build verification (wheel + sdist + py.typed)
- [x] Docker image for on-premise deployment
- [x] Run fine-tuning on GPU compute (QLoRA CodeLlama-7B on Colab T4)
- [x] Publish model to HuggingFace (WwzFwz/cobol-explain-7b)
- [x] Publish package to PyPI (v0.3.0, v0.3.1)
- [x] Comprehensive test suite (331 tests, 91% coverage, CI coverage gate)

---

## Success Metrics

- Parse success rate on sample corpus across sources
- Business rules extraction accuracy vs manual review
- Analysis time per 1000 lines of COBOL
- Number of tokens saved vs sending raw COBOL to the API
- Ability to handle COPYBOOKs and nested call chains
- Can run fully offline with a local model
- All JSON artifacts valid against the active schema version
- Run output can be re-consumed without running the parser again

---

## Testing Strategy

The testing plan for MVP must be concrete and automated.

### 1. Dialect Corpus Tests

- At least 10 COBOL programs from multiple sources: IBM, Open Mainframe Project,
  Rosetta Code, and fixed-format samples
- Parser must be tested on variations of fixed-format, free-format, `COPY`, `CALL`,
  `COMP-3`, `REDEFINES`, and `OCCURS`
- Each sample is labeled with the capabilities it covers

### 2. Contract Tests

- Every JSON artifact must pass schema validation in `contracts/`
- `manifest.json` must always be valid even when a run fails
- Output shape changes without a schema update must be treated as a failure

### 3. Regression Tests

- For main sample programs, expected output is committed to the repo
- If AST, rules, or graph change, the test must show a clear diff
- Regression tests are used to prevent parser refactors from breaking previous output

### 4. LLM Evaluation Tests

- Compare raw LLM output vs output with preprocessing
- Measure accuracy, token usage, and traceability
- LLM tests must not be the sole evidence that the pipeline works

---

## Out Of Scope For MVP

These items are important, but do not need to be built now:

- Full multi-user project persistence
- Enterprise RBAC and auth
- Full auth, RBAC, and platform-level approval workflow
- Full interactive GUI
- Production fine-tuned model
- Perfect dynamic `CALL` resolution for all cases

---

## Dataset For Development And Testing

- [Open Mainframe Project - COBOL Programming Course](https://github.com/openmainframeproject/cobol-programming-course)
- [IBM COBOL Samples](https://github.com/IBM/IBM-Z-zOS)
- [Rosetta Code - COBOL](https://rosettacode.org/wiki/Category:COBOL)
- COBOL programs from publicly available academic papers
