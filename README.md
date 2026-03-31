# cobol-intel

Open-source platform for understanding, documenting, and analyzing legacy COBOL
codebases using static analysis and LLM, fully on-premise capable.

## Why

Banks and fintechs running legacy COBOL systems face a common problem: the
developers who understood the system have retired, documentation is thin, and
nobody wants to touch critical code without knowing the impact. This tool helps
teams understand what their COBOL code actually does before migration or change
decisions are made.

## How It Works

```text
COBOL source files
      |
      v
[Parser & AST]          - understand structure programmatically
      |
      v
[COPYBOOK Resolver]     - resolve external dependencies
      |
      v
[Analysis Pipeline]     - extract business rules and build call graphs
      |
      v
[LLM Engine]            - generate human-readable explanations (optional)
      |
      v
Artifacts: JSON, Markdown docs, dependency graphs, business rules
```

The LLM only receives clean, structured input, not raw COBOL. This keeps
explanations more accurate and traceable back to source artifacts.

## Status

> Early development - Phase 2 ready
> Phase 1 static analysis core is complete: parser, call graph, rules
> extraction, artifact writing, and regression baselines are in place.

See [docs/PROGRESS.md](docs/PROGRESS.md) for the current implementation status.

## Current COBOL Coverage

The current parser is intentionally scoped to a practical MVP subset. It is
tested on committed samples that cover:

- fixed-format and free-format source
- `COPY`, circular copy detection, and `COPY ... REPLACING`
- `WORKING-STORAGE`, `FILE`, and `LINKAGE` sections
- `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, and level-88 conditions
- `PROCEDURE DIVISION USING`
- `IF`, `EVALUATE`, `PERFORM`, `CALL`, `STRING`, `UNSTRING`, `INSPECT`,
  `GOBACK`, and `STOP RUN`
- file I/O statements: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- `EXEC SQL` subset suitable for static analysis context extraction

Known gaps that remain future work include:

- `PERFORM THRU`, `GO TO`, and other legacy control-flow variants
- `EXEC CICS`
- broader `EXEC SQL` coverage for more complex statements and vendor-specific syntax
- `SEARCH`, `SEARCH ALL`, and richer `INSPECT` / `UNSTRING` variants
- `OCCURS DEPENDING ON`, `INDEXED BY`, `RENAMES`, and other enterprise dialect features

## Quick Start

```bash
pip install -e ".[dev]"

# Analyze a COBOL file or directory
cobol-intel analyze samples --copybook-dir copybooks

# Build graph artifacts
cobol-intel graph samples --copybook-dir copybooks
```

## On-Premise Deployment

The static analysis pipeline runs locally. Future LLM integrations are intended
to support both external APIs and local runtimes such as Ollama.

## Documentation

- [Project Plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Architecture Decisions](docs/DECISIONS.md)
- [Parser Evaluation](docs/PARSER_EVALUATION.md)
- [Research & Domain Knowledge](docs/RESEARCH.md)
- [Progress](docs/PROGRESS.md)
- [Suite Vision](docs/SUITE_VISION.md)

## License

MIT
