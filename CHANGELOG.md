# Changelog

All notable changes to cobol-intel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.1] - 2026-04-03

### Added

- **Dialect expansion**: `PERFORM THRU/THROUGH` range support with inclusive
  paragraph expansion in CFG builder and dead code detector
- **Dialect expansion**: `EXEC CICS` block-level extraction for static analysis
  context on mainframe transaction programs
- Fine-tuned COBOL explanation model on HuggingFace (`WwzFwz/cobol-explain-7b`)
  — QLoRA CodeLlama-7B trained on pipeline-generated instruction pairs
- Google Colab notebook for end-to-end fine-tuning (`notebooks/finetune_colab.ipynb`)
- CI coverage gate at 85% with `antlr_gen/` excluded from coverage metrics
- CI now lints `tools/` alongside `src/` and `tests/`
- Community governance files: CODE_OF_CONDUCT, LICENSE, SECURITY.md, SUPPORT.md
- Fine-tuning dataset builder (`tools/dataset_builder.py`) — generates
  Alpaca/ShareGPT instruction-tuning pairs from the analysis pipeline
- LoRA/PEFT fine-tuning script (`tools/finetune.py`) — CodeLlama-7B compatible,
  QLoRA support, checkpoint resume, reproducible config saving
- Local fine-tuned model backend (`llm/local_backend.py`) — loads PEFT or
  standard HuggingFace models for fully offline inference
- Prompt strategy comparison in benchmark (`tools/benchmark.py --compare`)
- `py.typed` marker for PEP 561 typed package support

### Changed

- Trust hardening: contract drift between CLI/API/service resolved, run metrics
  written for both analyze and explain paths, exponential backoff with jitter,
  cache keys include `tool_version` and `analysis_hash`, parallel workers use
  `backend.clone()` for thread safety
- Coverage config excludes generated ANTLR code for accurate metrics (91%)
- Test suite expanded to 331 tests

### Fixed

- pyproject.toml TOML ordering: `dependencies` was incorrectly nested under
  `[project.urls]` instead of `[project]`, causing `uv build` to fail
- Local backend defaults are now deterministic and install guidance points to
  package extras for offline inference and training
- Governance now treats the `local` backend as `local_only` for policy and
  redaction decisions

## [0.3.0] - 2026-04-01

### Added

- **Control flow graph (CFG) builder**: intra-program CFG with basic blocks, branch/perform/
  fallthrough edges, and unsupported construct warnings (GO TO, ALTER)
- **Field reference indexer**: per-statement read/write/condition/call_param classification
  with aggregated field usage counts
- **Data flow analyzer**: directed field-to-field flow graph covering MOVE, COMPUTE,
  READ INTO, WRITE FROM, REWRITE FROM, and CALL USING — with Mermaid diagram output
- **Dead code detector**: unreachable paragraph detection via BFS reachability, unused
  data item scanning, and trivially dead branch detection (constant conditions)
- Pipeline now writes `analysis/` artifacts (CFG, data flow, dead code, references)
  for every parsed program
- Doc generator includes data flow diagrams and dead code findings sections
- `ArtifactIndex` in manifest now tracks `analysis` artifacts

### Changed

- Hardened API ergonomics with a module-level FastAPI app export, version response parity,
  structured error payloads, and richer run summaries
- Made explanation cache keys safer against stale outputs by including a context revision
- Synced progress and fintech-readiness docs with the actual Phase 3 feature set
- Version bumped to 0.3.0

### Fixed

- Fixed `make serve-api` to point at a real FastAPI app object
- Made `make clean` portable by using Python stdlib instead of Unix-only shell commands

## [0.2.0] - 2026-04-01

### Added

- Read-only REST API with versioned endpoints (`/api/v1/`)
- Structured error codes (`ErrorCode` enum) for operational monitoring
- Cross-platform CI pipeline (Linux + Windows, Python 3.11 + 3.12)
- Benchmark suite for parse success rate, latency, and token savings
- Per-program documentation generator (Markdown + HTML)
- Self-contained HTML report with sidebar navigation, search, and Mermaid graphs
- Change impact analyzer with call graph traversal and field reference scanning
- Parallel LLM processing with bounded backend-specific concurrency
- File-based explanation cache with composite invalidation keys
- Docker image and docker-compose with optional Ollama sidecar
- CLI commands: `impact`, `docs`
- CLI flags: `--parallel`, `--max-workers`, `--cache/--no-cache`, `--format`
- `Makefile` with common targets: lint, test, bench, build, serve-api
- PyPI publish workflow on tag push
- Output gallery and API guide documentation
- `CHANGELOG.md`, `CONTRIBUTING.md`, and GitHub issue templates

## [0.1.0] - 2026-03-31

### Added

- ANTLR4-based COBOL parser with fixed-format and free-format support
- COPYBOOK resolver with circular dependency detection
- Call graph builder and business rules extractor
- Multi-backend LLM explanation engine (Claude, OpenAI, Ollama)
- Context builder with smart chunking and token budget awareness
- Governance layer: audit logging, sensitivity classification, prompt redaction
- Strict policy enforcement and configurable model registry
- Backend retry/timeout and token budget controls
- CLI commands: `analyze`, `explain`, `graph`
- Versioned JSON artifact contracts with Pydantic v2
