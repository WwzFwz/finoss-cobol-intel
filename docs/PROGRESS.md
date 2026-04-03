# Progress Tracker

Project work log. Updated every work session.

---

## Current Status

**Phase**: 4 - Fine-Tuning Infrastructure And Packaging (in progress)
**Started**: 2026-03-31
**Target MVP**: -
**Test Status**: 331/331 pass (91% coverage)

Notes:

- Phase 0 and 1 complete: parser, analysis, artifacts, CLI analyze/graph.
- Phase 2 complete: LLM backend interface, Claude + OpenAI + Ollama backends, context builder,
  explanation engine (3 modes), traceability, evaluation test, CLI explain command.
- Additional hardening complete: manifest stays consistent when some explains fail,
  top-level summary has source refs, prompt budgeting better preserves rules/graph,
  and paragraph explanation count is capped to keep cost/latency under control.
- Phase 3 governance foundations landed: audit/event log, manifest governance,
  sensitivity scoring, approved model registry, and redaction helper.
- Further hardening landed: strict policy enforcement, token budget cap,
  configurable JSON policy config, and basic retry/timeout for all backends.
- Phase 3 now covers versioned API, documentation generator, HTML report,
  impact analyzer, parallel explain, cache layer, Docker, and CI.
- Deep analysis layer complete: CFG builder, data flow analyzer, dead code
  detector, and reference indexer — all integrated into pipeline and docs.
- Trust hardening complete: contract drift CLI/API/service resolved, run metrics
  for both analysis and explain, exponential backoff with jitter, cache key
  with tool_version + analysis_hash, parallel backend clone, clean lint baseline.
- Dialect expansion added: `PERFORM THRU` and basic `EXEC CICS` block
  extraction are now supported by the parser and regression tests.
- Next focus shifts to reproducibility, packaging extras, local-model
  governance, and real training verification on compute/GPU.

---

## Checklist Per Phase

### Phase 0 - Foundation

*Gate: this phase is complete after the parser comparison is done and the parser decision is locked in ADR-006.*

**Project Setup**

- [x] Create folder structure following package boundaries (`src/cobol_intel/core`, `contracts`, `parsers`, `analysis`, `llm`, `outputs`, `service`, `cli`)
- [x] Setup `pyproject.toml` with dependency management
- [x] Setup virtual environment
- [x] Setup linting boundaries with `tach`

**Dataset**

- [x] Collect initial COBOL samples for fixed-format, free-format, `COPY`, `COMP-3`, `REDEFINES`, and `CALL`
- [x] Categorize samples for parser PoC corpus
- [x] At least 5 samples available before parser comparison is locked

**Parser PoC (Decision Gate)**

- [x] Implement minimal PoC with `lark` on initial corpus samples
- [x] Implement minimal PoC with ANTLR4 COBOL grammar on the same samples
- [x] Write evaluation report comparing `lark` vs ANTLR4
- [x] Lock parser choice in `DECISIONS.md` ADR-006 - **Accepted: ANTLR4**

**Contracts**

- [x] Define `manifest.json` schema in `contracts/`
- [x] Define final `run_id` format and document in ADR-014
- [x] Define minimal validated AST output schema (`contracts/ast_output.py`)
- [x] Write first contract test validating manifest schema

**Error Handling Strategy**

- [x] Implement end-to-end error handling per ADR-013
- [x] `manifest.json` supports `status: partially_completed` with `warnings` and `errors`

---

### Phase 1 - Static Analysis Core

*Gate: all corpus tests must pass, main artifacts must be produced, and regression baseline must be forming.*

**Parser**

- [x] Complete parser: IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE DIVISION
- [x] Handle basic fixed-format preprocessing
- [x] Handle samples with `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, and `COPY`
- [x] Initial corpus tests for parser samples run without crashes

**Resolver And Graph**

- [x] Initial COPYBOOK resolver for preprocessing
- [x] Circular dependency detection between COPYBOOKs
- [x] CALL graph builder for static calls
- [x] Dependency graph output: JSON adjacency list + Mermaid diagram

**Business Rules**

- [x] Extractor for `IF` and `EVALUATE` conditions in PROCEDURE DIVISION
- [x] JSON business rules output validated against schema

**Artifacts And Service**

- [x] Consistent JSON artifact writer to artifact directory
- [x] Basic service pipeline for parse -> analyze -> write artifacts
- [x] CLI `analyze` and `graph` use service layer

**Testing**

- [x] Corpus test suite: at least 10 COBOL programs from different sources
- [x] Contract test suite for manifest, AST, graph, rules, and run_id
- [x] Regression test: expected parser/artifact output committed and kept stable
- [x] Integration test for Phase 1 artifact pipeline

---

### Phase 2 - LLM Integration

- [x] `LLMBackend` abstract interface in `llm/backend.py`
- [x] `ClaudeBackend` implementation (`llm/claude_backend.py`)
- [x] `OllamaBackend` implementation (`llm/ollama_backend.py`)
- [x] Context builder: AST + rules + graph -> LLM-ready prompt (`llm/context_builder.py`)
- [x] Smart chunker based on paragraph/section structure (truncation + per-paragraph prompts)
- [x] Explanation engine mode `technical`
- [x] Explanation engine mode `business`
- [x] Explanation engine mode `audit`
- [x] All LLM output includes traceability to source artifact (`ParagraphExplanation.source`)
- [x] Evaluation test: raw LLM vs pipeline + LLM on the same sample

---

### Phase 3 - Output And Polish

- [x] Audit/event log artifact for analysis and explain runs
- [x] Governance summary in manifest
- [x] Approved model registry + preset helper
- [x] Sensitivity classification helper
- [x] Redaction helper for sensitive cloud prompts
- [x] Strict policy enforcement for sensitive workloads on cloud backends
- [x] Token budget per explain run
- [x] Basic retry / timeout for OpenAI, Claude, and Ollama backends
- [x] Configurable policy registry via JSON config
- [x] Documentation generator Markdown output per program
- [x] HTML report generator
- [x] Change impact analyzer
- [x] Deep analysis: CFG builder, data flow analyzer, dead code detector, reference indexer
- [x] Complete and documented CLI interface
- [x] README with feature overview and CLI usage
- [x] Docker image for on-premise deployment
- [x] `CHANGELOG.md` and versioning strategy (bumped to 0.3.0)

---

### Phase 4 - Fine-Tuning Infrastructure And Packaging

- [x] Fine-tuning dataset builder (`tools/dataset_builder.py`)
- [x] LoRA/PEFT fine-tuning script (`tools/finetune.py`)
- [x] Local fine-tuned model backend (`llm/local_backend.py`)
- [x] Prompt comparison benchmark (`raw source` vs `structured pipeline`)
- [x] PyPI build verified (wheel + sdist + py.typed)
- [x] Fixed pyproject.toml TOML ordering bug (dependencies under project.urls)
- [x] Read-only API prototype (already present from Phase 3)
- [x] Optional extras for `local` and `train`
- [x] Local backend defaults made deterministic for reproducible offline runs
- [x] Run fine-tuning on GPU (QLoRA CodeLlama-7B on Colab T4)
- [x] Publish fine-tuned model to HuggingFace (WwzFwz/cobol-explain-7b)
- [x] Publish package to PyPI (v0.3.0, v0.3.1)

---

## Session Log

### 2026-03-31

- Discussed concept, problem statement, architecture, and fintech pain points
- Created: `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/RESEARCH.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`
- Technical feedback review from peer and major updates to planning docs
- Added `docs/SUITE_VISION.md` to maintain long-term suite direction without expanding MVP scope

### 2026-03-31 - Phase 0 Stabilization

- Ran test suite from `.venv`
- Found error with `tmp_path` pytest due to denied access to Windows temp directory
- Changed copybook test to use static fixture in repo instead of runtime temporary directory
- Cleaned up pytest config by disabling default `cacheprovider` that triggered permission warnings on Windows
- Rerun suite green

### 2026-03-31 - ANTLR4 PoC And ADR-006

- Implemented ANTLR4 grammar and parser wrapper
- Wrote `docs/PARSER_EVALUATION.md` for Lark vs ANTLR4 comparison
- ADR-006 locked: **Accepted: ANTLR4** as default parser

### 2026-03-31 - Phase 1 Core Implementation

- Implemented `analysis.call_graph` with adjacency list
- Implemented `analysis.rules_extractor` for `IF`, `EVALUATE`, and `CONDITION-88`
- Implemented `outputs.writers` for JSON/text artifacts and summary Markdown
- Implemented `service.pipeline` for parse -> analyze -> write artifacts
- Added integration test for artifact pipeline
- Connected CLI `analyze` and `graph` to service layer
- Rerun suite: **100/100 pass**

### 2026-03-31 - Phase 1 Completion

- Hardened grammar parser for `ENVIRONMENT DIVISION`, `FILE SECTION`,
  `LINKAGE SECTION`, `SELECT/ASSIGN`, `FD`, and `GOBACK`
- Added circular `COPY` detection in preprocessor with stable warnings
- Added 3 new sample programs bringing committed corpus to 10 files
- Added corpus smoke test for ANTLR4 and Lark across entire sample corpus
- Added committed regression baseline for AST, rules, and call graph
- Rerun suite: **124/124 pass**

### 2026-03-31 - Parser Coverage Expansion

- Added parser support for `EXEC SQL`
- Added file I/O statements: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- Added `COPY ... REPLACING` in preprocessor
- Added `PROCEDURE DIVISION USING` to parse result and AST artifact
- Added `UNSTRING` and `INSPECT` support
- Added new corpus samples for SQL, file batch, and copybook replacing
- Rerun suite: **134/134 pass**

### 2026-03-31 - Phase 2 LLM Integration

- Implemented `LLMBackend` abstract interface and `LLMResponse` dataclass
- Implemented `ClaudeBackend` (Anthropic SDK) and `OllamaBackend` (local model)
- Implemented `context_builder.py` — transforms Phase 1 artifacts to structured prompts
  with system prompt per mode (technical/business/audit) and smart truncation
- Implemented `explainer.py` — orchestrates context builder + backend, produces
  `ExplanationOutput` with traceability via `SourceRef` per paragraph
- Implemented `service/explain.py` — service layer for Phase 1 + LLM explanation
- CLI `explain` command now fully functional with `--model` and `--mode` flags
- CLI `analyze` now optionally runs LLM explanation via `--model` flag
- Contract: `ExplanationOutput` schema with `ParagraphExplanation` and traceability
- Tests: contract (5), context builder (10), explainer mock (7), evaluation (5)
- Rerun suite: **164/164 pass**

### 2026-04-01 - Governance Foundations

- Added new contracts for governance and audit events
- Manifest now stores governance summary and artifact logs
- Service layer now writes `logs/audit_events.jsonl` for analysis and explain runs
- Added approved model registry + preset helper for `claude`, `openai`, and `ollama`
- Added sensitivity classifier and redaction helper for cloud prompts
- Added unit/contract tests for governance, policy, and audit logging
- Rerun suite: **186/186 pass**

### 2026-04-01 - Policy Enforcement And Backend Resilience

- Added `config/llm_policy.json` as default policy registry that can be overridden
- Added strict policy enforcement to block cloud explain on sensitive artifacts
- Added token budget enforcement in `service/explain.py`
- Added basic retry + timeout for Claude, OpenAI, and Ollama backends
- Added broader redaction patterns for common PII fields
- Added tests for policy config, strict block, token budget, and retry behavior
- Rerun suite: **190/190 pass**

### 2026-04-02 - Phase 4: Fine-Tuning Infrastructure And PyPI Readiness

- Implemented `tools/dataset_builder.py`: generates instruction-tuning JSONL
  from pipeline output (80 samples from 13 programs — program-level, paragraph,
  data flow, dead code pairs). Supports Alpaca and ShareGPT formats.
- Implemented `tools/finetune.py`: LoRA/PEFT training script for
  CodeLlama-7B or similar models. Supports 4-bit QLoRA, checkpoint resume,
  train/eval split, and reproducible config saving.
- Implemented `src/cobol_intel/llm/local_backend.py`: backend adapter for
  loading fine-tuned HuggingFace models locally. Auto-detects PEFT models,
  Alpaca prompt template matching finetune.py.
- CLI update: added `--model local` to analyze and explain commands.
- PyPI readiness: added `py.typed` marker (PEP 561), fixed pyproject.toml
  TOML ordering bug (`dependencies` wrongly nested under `[project.urls]`), verified
  clean wheel build (`uv build` → sdist + wheel).
- Benchmark expansion: added `--compare` flag for raw vs pipeline prompt
  strategy comparison (structured sections, traceability, rules reference).
- Early Phase 4 hardening: `local` backend now recognized as
  `local_only`, packaging extras `.[local]` and `.[train]` added,
  and benchmark/docs cleaned up to not overclaim as live model eval.
- Parse success rate: 13/13 (100%), avg token savings: 28.6%
- Rerun suite: **318/318 pass**, tach boundaries OK

### 2026-04-01 - Phase 3 Completion: Polish And Packaging

- Bumped version to 0.3.0 (pyproject.toml + `__init__.py`)
- Updated CHANGELOG.md with all 0.3.0 features
- CLI polish: added `--version` / `-V` flag, improved help text for all commands
- Hardened Dockerfile: multi-stage build, non-root user, health check, CLI entrypoint
- docker-compose update: override entrypoint for API mode
- README update: added deep analysis features, `analysis/` dir in artifact tree, `--version`
- Rerun suite: **313/313 pass**, tach boundaries OK

### 2026-04-01 - Deep Analysis Layer And Pipeline Integration

- Implemented 4 new analysis modules:
  - **CFG Builder**: intra-program control flow graph with basic blocks, branch/perform/fallthrough edges
  - **Reference Indexer**: field-level read/write/condition/call_param classification per statement
  - **Data Flow Analyzer**: directed field-to-field data flow graph (MOVE, COMPUTE, READ INTO, WRITE FROM, CALL USING)
  - **Dead Code Detector**: unreachable paragraphs (BFS reachability), unused data items, trivially dead branches
- Added contracts: `cfg_output.py`, `data_flow_output.py`, `dead_code_output.py`, `reference_output.py`
- Added `analysis` field in `ArtifactIndex` manifest for tracking new analysis artifacts
- Integrated into `pipeline.py`: every successfully parsed program now produces
  reference index, CFG, data flow graph (JSON + Mermaid), and dead code report
- Integrated into doc generator: program docs now include data flow diagram and dead code findings
- Integrated into doc service: loads analysis artifacts from completed runs for docs generation
- Updated integration test to verify analysis artifacts are written to disk
- Added 57 new tests (unit + contract) for 4 analysis modules
- Rerun suite: **313/313 pass**, tach boundaries OK

---

### 2026-04-03 - Trust Hardening And CI Hygiene

- Trust hardening: contract drift CLI/API/service, run metrics both paths,
  exponential backoff + jitter, cache key with tool_version + analysis_hash,
  parallel backend clone pattern, clean lint baseline.
- CI strengthened: coverage gate 85%, lint now includes `tools/`,
  coverage config excludes `antlr_gen/`.
- Docs hygiene: PROGRESS.md test count updated to 326, ADR-013 checklist
  marked complete (implementation sufficient).
- Rerun suite: **326/326 pass**, 91% coverage, ruff clean, tach OK

---

### 2026-04-03 - Fine-Tuning And PyPI Release

- Fine-tuning successful: QLoRA CodeLlama-7B on Colab T4, 3 epochs,
  ~80 training samples from 14 COBOL programs.
- Model published to HuggingFace: `WwzFwz/cobol-explain-7b`
- Package published to PyPI: v0.3.0 (initial), v0.3.1 (dialect + fine-tuning)
- Dialect expansion: `PERFORM THRU` and `EXEC CICS` added to parser
- Colab notebook added for reproducible fine-tuning
- Rerun suite: **331/331 pass**, 91% coverage, ruff clean, tach OK

---

## Blockers And Open Questions

- All Phase 0-4 items are complete
- Extended `EXEC SQL` and `SEARCH/SEARCH ALL` dialect can still be added later
- Sanity test for fine-tuned model not yet run due to OOM on Colab (needs a new session)

---

## Useful Resources

- `tests/corpus/test_parser_poc.py` as Lark PoC baseline
- `tests/corpus/test_antlr4_poc.py` as ANTLR4 PoC baseline
- `tests/unit/test_call_graph.py` for graph extraction
- `tests/unit/test_rules_extractor.py` for business rules extraction
- `tests/integration/test_service_pipeline.py` for artifact pipeline end-to-end
