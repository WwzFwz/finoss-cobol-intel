# cobol-intel

`cobol-intel` is an open-source static analysis and documentation engine for
legacy COBOL codebases. It is designed for banking, fintech, and regulated
modernization workflows where teams need traceable artifacts before they trust
an LLM with explanation or migration support.

## Why This Exists

Legacy COBOL systems often fail the same way:

- key maintainers retire
- documentation is stale or missing
- impact analysis is manual and risky
- regulators or auditors still expect clear explanations

`cobol-intel` addresses that by building a structured pipeline first:

```text
COBOL source
   -> preprocessing and copybook resolution
   -> parser and AST
   -> call graph and business rules
   -> versioned JSON and Markdown artifacts
   -> optional LLM explanation layer
```

The core idea is simple: the LLM should consume clean, traceable artifacts, not
raw COBOL.

## Current Status

- Phase 0 complete: parser evaluation, contracts, and project foundations
- Phase 1 complete: static analysis core, artifact writing, corpus coverage, and regression baselines
- Phase 2 ready: LLM backend abstraction and explanation workflows are the next major step

See [docs/PROGRESS.md](docs/PROGRESS.md) for the implementation timeline.

## What It Supports Today

The current committed corpus covers a practical modernization subset:

- fixed-format and free-format COBOL
- `COPY`, circular copy detection, and `COPY ... REPLACING`
- `WORKING-STORAGE`, `FILE`, and `LINKAGE` sections
- `PROCEDURE DIVISION USING`
- `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, and level-88 conditions
- `IF`, `EVALUATE`, `PERFORM`, `CALL`, `STRING`, `UNSTRING`, `INSPECT`
- file I/O statements: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- `EXEC SQL` subset for static-analysis context extraction

Known gaps still remain for richer enterprise dialects such as `EXEC CICS`,
`PERFORM THRU`, `SEARCH`, `SEARCH ALL`, and broader vendor-specific SQL/COBOL
syntax. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the detailed gap list.

## Installation

```bash
pip install -e ".[dev]"
```

Requirements:

- Python 3.11+
- Java only if you want to regenerate the ANTLR parser files

## CLI Usage

The current CLI is intentionally small and focused on artifact generation.

### Inspect Available Commands

```bash
cobol-intel --help
cobol-intel analyze --help
cobol-intel graph --help
```

### Analyze A Sample Directory

```bash
cobol-intel analyze samples --copybook-dir copybooks
```

Typical result:

```text
[cobol-intel] analyze: samples
Run ID: run_20260331_001
Status: completed
Artifacts: artifacts/samples/run_20260331_001
```

### Analyze A Single Program

```bash
cobol-intel analyze samples/complex/sqlops.cbl --copybook-dir copybooks
```

### Write Artifacts To A Custom Directory

```bash
cobol-intel analyze samples --copybook-dir copybooks --output build/artifacts
```

### Generate Graph Artifacts Only

```bash
cobol-intel graph samples --copybook-dir copybooks
```

### Explain Command

```bash
cobol-intel explain samples/complex/payment.cbl --model claude --mode technical
```

`explain` is currently a Phase 2 placeholder. The static-analysis pipeline is
already functional; the LLM-facing explanation layer is the next planned stage.

## Output Artifacts

Each analysis run writes a stable artifact tree that can be consumed later by a
GUI, API, or downstream automation:

```text
artifacts/<project_slug>/<run_id>/
  manifest.json
  ast/
  graphs/
  rules/
  docs/
```

For a concrete example, see [docs/ARTIFACT_EXAMPLE.md](docs/ARTIFACT_EXAMPLE.md).

## Naming And Positioning

To keep the project publish-ready and consistent:

- repository name: `cobol-intel`
- CLI command: `cobol-intel`
- Python package: `cobol_intel`

Long term, this project may become the first module in a broader finance OSS
suite. That future positioning is intentional, but the current public identity
remains `cobol-intel`. In other words, the suite idea is optional; this repo is
already meant to stand on its own.

More detail is in [docs/SUITE_VISION.md](docs/SUITE_VISION.md).

## Documentation

- [Project Plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Architecture Decisions](docs/DECISIONS.md)
- [Parser Evaluation](docs/PARSER_EVALUATION.md)
- [Artifact Example](docs/ARTIFACT_EXAMPLE.md)
- [Research](docs/RESEARCH.md)
- [Progress](docs/PROGRESS.md)
- [Suite Vision](docs/SUITE_VISION.md)

## License

MIT
