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
