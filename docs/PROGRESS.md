# Progress Tracker

Log pengerjaan project. Update setiap sesi kerja.

---

## Status Saat Ini

**Fase**: 4 - Fine-Tuning Infrastructure And Packaging (in progress)
**Mulai**: 2026-03-31
**Target MVP**: -
**Test Status**: 331/331 pass (91% coverage)

Catatan:

- Fase 0 dan 1 selesai: parser, analysis, artifacts, CLI analyze/graph.
- Fase 2 selesai: LLM backend interface, Claude + OpenAI + Ollama backends, context builder,
  explanation engine (3 modes), traceability, evaluation test, CLI explain command.
- Hardening tambahan selesai: manifest tetap konsisten saat sebagian explain gagal,
  top-level summary punya source refs, prompt budgeting lebih menjaga rules/graph,
  dan jumlah paragraph explanation dibatasi agar cost/latency tetap terkendali.
- Fondasi governance Phase 3 sudah mulai masuk: audit/event log, manifest governance,
  sensitivity scoring, approved model registry, dan redaction helper.
- Hardening berikutnya sudah masuk: strict policy enforcement, token budget cap,
  configurable JSON policy config, dan retry/timeout dasar untuk semua backend.
- Phase 3 sekarang sudah mencakup versioned API, documentation generator,
  HTML report, impact analyzer, parallel explain, cache layer, Docker, dan CI.
- Deep analysis layer selesai: CFG builder, data flow analyzer, dead code
  detector, dan reference indexer — semua terintegrasi ke pipeline dan docs.
- Trust hardening selesai: contract drift CLI/API/service diperbaiki, run metrics
  untuk analysis dan explain, retry/backoff exponential dengan jitter, cache key
  dengan tool_version + analysis_hash, parallel backend clone, lint baseline bersih.
- Dialect expansion bertambah: `PERFORM THRU` dan basic `EXEC CICS` block
  extraction sekarang sudah didukung oleh parser dan regression tests.
- Fokus perbaikan berikutnya bergeser ke reproducibility, packaging extras,
  local-model governance, dan verifikasi training nyata pada compute/GPU.

---

## Checklist Per Fase

### Fase 0 - Fondasi

*Gate: fase ini selesai setelah parser comparison selesai dan keputusan parser dikunci di ADR-006.*

**Project Setup**

- [x] Buat struktur folder sesuai package boundary (`src/cobol_intel/core`, `contracts`, `parsers`, `analysis`, `llm`, `outputs`, `service`, `cli`)
- [x] Setup `pyproject.toml` dengan dependency management
- [x] Setup virtual environment
- [x] Setup linting boundary dengan `tach`

**Dataset**

- [x] Kumpulkan sample COBOL awal untuk fixed-format, free-format, `COPY`, `COMP-3`, `REDEFINES`, dan `CALL`
- [x] Kategorisasi sample untuk corpus parser PoC
- [x] Minimal 5 sample tersedia sebelum parser comparison dikunci

**Parser PoC (Decision Gate)**

- [x] Implementasi PoC minimal dengan `lark` pada corpus sample awal
- [x] Implementasi PoC minimal dengan ANTLR4 COBOL grammar pada sample yang sama
- [x] Tulis evaluation report untuk perbandingan `lark` vs ANTLR4
- [x] Kunci pilihan parser di `DECISIONS.md` ADR-006 - **Accepted: ANTLR4**

**Contracts**

- [x] Definisikan `manifest.json` schema di `contracts/`
- [x] Definisikan `run_id` format final dan catat ke ADR-014
- [x] Definisikan AST output schema minimal yang tervalidasi (`contracts/ast_output.py`)
- [x] Tulis contract test pertama yang validasi schema manifest

**Error Handling Strategy**

- [x] Implementasikan error handling end-to-end sesuai ADR-013
- [x] `manifest.json` mendukung `status: partially_completed` beserta `warnings` dan `errors`

---

### Fase 1 - Static Analysis Core

*Gate: semua corpus test harus pass, artifact utama harus keluar, dan regression baseline mulai terbentuk.*

**Parser**

- [x] Parser lengkap: IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE DIVISION
- [x] Handle fixed-format preprocessing dasar
- [x] Handle sample dengan `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, dan `COPY`
- [x] Corpus test awal untuk sample parser berjalan tanpa crash

**Resolver And Graph**

- [x] COPYBOOK resolver awal untuk preprocessing
- [x] Deteksi circular dependency antar COPYBOOK
- [x] CALL graph builder untuk static calls
- [x] Dependency graph output: JSON adjacency list + Mermaid diagram

**Business Rules**

- [x] Extractor untuk `IF` dan `EVALUATE` conditions di PROCEDURE DIVISION
- [x] Output JSON business rules tervalidasi terhadap schema

**Artifacts And Service**

- [x] JSON artifact writer yang konsisten ke artifact directory
- [x] Service pipeline dasar untuk parse -> analyze -> write artifacts
- [x] CLI `analyze` dan `graph` memakai service layer

**Testing**

- [x] Corpus test suite: minimal 10 program COBOL dari sumber berbeda
- [x] Contract test suite untuk manifest, AST, graph, rules, dan run_id
- [x] Regression test: expected output parser/artifact di-commit dan dijaga stabil
- [x] Integration test untuk Phase 1 artifact pipeline

---

### Fase 2 - LLM Integration

- [x] `LLMBackend` abstract interface di `llm/backend.py`
- [x] `ClaudeBackend` implementation (`llm/claude_backend.py`)
- [x] `OllamaBackend` implementation (`llm/ollama_backend.py`)
- [x] Context builder: AST + rules + graph -> LLM-ready prompt (`llm/context_builder.py`)
- [x] Smart chunker berbasis struktur paragraph/section (truncation + per-paragraph prompts)
- [x] Explanation engine mode `technical`
- [x] Explanation engine mode `business`
- [x] Explanation engine mode `audit`
- [x] Semua output LLM include traceability ke artifact sumber (`ParagraphExplanation.source`)
- [x] Evaluation test: raw LLM vs pipeline + LLM pada sample yang sama

---

### Fase 3 - Output And Polish

- [x] Audit/event log artifact untuk analysis dan explain runs
- [x] Governance summary pada manifest
- [x] Approved model registry + preset helper
- [x] Sensitivity classification helper
- [x] Redaction helper untuk prompt cloud yang sensitif
- [x] Strict policy enforcement untuk workload sensitif pada backend cloud
- [x] Token budget per explain run
- [x] Retry / timeout dasar untuk backend OpenAI, Claude, dan Ollama
- [x] Configurable policy registry via JSON config
- [x] Documentation generator output Markdown per program
- [x] HTML report generator
- [x] Change impact analyzer
- [x] Deep analysis: CFG builder, data flow analyzer, dead code detector, reference indexer
- [x] CLI interface lengkap dan terdokumentasi
- [x] README dengan feature overview dan CLI usage
- [x] Docker image untuk on-premise deployment
- [x] `CHANGELOG.md` dan versioning strategy (bumped to 0.3.0)

---

### Fase 4 - Fine-Tuning Infrastructure And Packaging

- [x] Fine-tuning dataset builder (`tools/dataset_builder.py`)
- [x] LoRA/PEFT fine-tuning script (`tools/finetune.py`)
- [x] Local fine-tuned model backend (`llm/local_backend.py`)
- [x] Prompt comparison benchmark (`raw source` vs `structured pipeline`)
- [x] PyPI build verified (wheel + sdist + py.typed)
- [x] Fixed pyproject.toml TOML ordering bug (dependencies under project.urls)
- [x] Read-only API prototype (sudah ada dari Phase 3)
- [x] Optional extras untuk `local` dan `train`
- [x] Local backend default dibuat deterministik untuk reproducible offline runs
- [x] Run fine-tuning pada GPU (QLoRA CodeLlama-7B on Colab T4)
- [x] Publish fine-tuned model ke HuggingFace (WwzFwz/cobol-explain-7b)
- [x] Publish package ke PyPI (v0.3.0, v0.3.1)

---

## Session Log

### 2026-03-31

- Diskusi konsep, problem statement, arsitektur, dan pain point fintech
- Dibuat: `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/RESEARCH.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`
- Review feedback teknis dari rekan dan update besar pada planning docs
- Tambah `docs/SUITE_VISION.md` untuk menjaga arah suite jangka panjang tanpa menambah scope MVP

### 2026-03-31 - Phase 0 Stabilization

- Jalankan test suite dari `.venv`
- Ditemukan error pada `tmp_path` pytest akibat akses ditolak ke Windows temp directory
- Ganti test copybook agar memakai fixture statis di repo, bukan temporary directory runtime
- Rapikan konfigurasi pytest dengan menonaktifkan `cacheprovider` default yang memicu warning permission di Windows
- Rerun suite hijau

### 2026-03-31 - ANTLR4 PoC And ADR-006

- Implementasi ANTLR4 grammar dan parser wrapper
- Tulis `docs/PARSER_EVALUATION.md` untuk comparison Lark vs ANTLR4
- ADR-006 dikunci: **Accepted: ANTLR4** sebagai parser default

### 2026-03-31 - Phase 1 Core Implementation

- Implementasi `analysis.call_graph` dengan adjacency list
- Implementasi `analysis.rules_extractor` untuk `IF`, `EVALUATE`, dan `CONDITION-88`
- Implementasi `outputs.writers` untuk JSON/text artifacts dan summary Markdown
- Implementasi `service.pipeline` untuk parse -> analyze -> write artifacts
- Tambah integration test untuk artifact pipeline
- Sambungkan CLI `analyze` dan `graph` ke service layer
- Rerun suite: **100/100 pass**

### 2026-03-31 - Phase 1 Completion

- Hardening grammar parser untuk `ENVIRONMENT DIVISION`, `FILE SECTION`,
  `LINKAGE SECTION`, `SELECT/ASSIGN`, `FD`, dan `GOBACK`
- Tambah circular `COPY` detection di preprocessor beserta warning yang stabil
- Tambah 3 sample program baru sehingga corpus committed menjadi 10 file
- Tambah corpus smoke test untuk ANTLR4 dan Lark pada seluruh sample corpus
- Tambah regression baseline committed untuk AST, rules, dan call graph
- Rerun suite: **124/124 pass**

### 2026-03-31 - Parser Coverage Expansion

- Tambah dukungan parser untuk `EXEC SQL`
- Tambah file I/O statements: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- Tambah `COPY ... REPLACING` di preprocessor
- Tambah `PROCEDURE DIVISION USING` ke parse result dan AST artifact
- Tambah dukungan `UNSTRING` dan `INSPECT`
- Tambah sample corpus baru untuk SQL, file batch, dan copybook replacing
- Rerun suite: **134/134 pass**

### 2026-03-31 - Phase 2 LLM Integration

- Implementasi `LLMBackend` abstract interface dan `LLMResponse` dataclass
- Implementasi `ClaudeBackend` (Anthropic SDK) dan `OllamaBackend` (local model)
- Implementasi `context_builder.py` — transforms Phase 1 artifacts ke structured prompts
  dengan system prompt per mode (technical/business/audit) dan smart truncation
- Implementasi `explainer.py` — orchestrates context builder + backend, produces
  `ExplanationOutput` dengan traceability via `SourceRef` per paragraph
- Implementasi `service/explain.py` — service layer untuk Phase 1 + LLM explanation
- CLI `explain` command sekarang fully functional dengan `--model` dan `--mode` flags
- CLI `analyze` sekarang bisa opsional run LLM explanation via `--model` flag
- Contract: `ExplanationOutput` schema dengan `ParagraphExplanation` dan traceability
- Tests: contract (5), context builder (10), explainer mock (7), evaluation (5)
- Rerun suite: **164/164 pass**

### 2026-04-01 - Governance Foundations

- Tambah contract baru untuk governance dan audit events
- Manifest sekarang menyimpan governance summary dan artifact logs
- Service layer sekarang menulis `logs/audit_events.jsonl` untuk analysis dan explain runs
- Tambah approved model registry + preset helper untuk `claude`, `openai`, dan `ollama`
- Tambah sensitivity classifier dan redaction helper untuk cloud prompts
- Tambah unit/contract tests untuk governance, policy, dan audit logging
- Rerun suite: **186/186 pass**

### 2026-04-01 - Policy Enforcement And Backend Resilience

- Tambah `config/llm_policy.json` sebagai policy registry default yang bisa dioverride
- Tambah strict policy enforcement untuk block cloud explain pada artifact sensitif
- Tambah token budget enforcement di `service/explain.py`
- Tambah retry + timeout dasar di backend Claude, OpenAI, dan Ollama
- Tambah redaction pattern yang lebih luas untuk field PII umum
- Tambah test untuk policy config, strict block, token budget, dan retry behavior
- Rerun suite: **190/190 pass**

### 2026-04-02 - Phase 4: Fine-Tuning Infrastructure And PyPI Readiness

- Implementasi `tools/dataset_builder.py`: generate instruction-tuning JSONL
  dari pipeline output (80 samples dari 13 programs — program-level, paragraph,
  data flow, dead code pairs). Support Alpaca dan ShareGPT format.
- Implementasi `tools/finetune.py`: LoRA/PEFT training script untuk
  CodeLlama-7B atau model sejenis. Support 4-bit QLoRA, checkpoint resume,
  train/eval split, dan reproducible config saving.
- Implementasi `src/cobol_intel/llm/local_backend.py`: backend adapter untuk
  load fine-tuned HuggingFace model secara lokal. Auto-detect PEFT model,
  Alpaca prompt template matching finetune.py.
- CLI update: tambah `--model local` ke analyze dan explain commands.
- PyPI readiness: tambah `py.typed` marker (PEP 561), fix pyproject.toml
  TOML ordering bug (`dependencies` salah masuk `[project.urls]`), verify
  wheel build clean (`uv build` → sdist + wheel).
- Benchmark expansion: tambah `--compare` flag untuk raw vs pipeline prompt
  strategy comparison (structured sections, traceability, rules reference).
- Hardening Phase 4 awal: backend `local` sekarang dikenali sebagai
  `local_only`, packaging extras `.[local]` dan `.[train]` ditambahkan,
  dan benchmark/docs dirapikan supaya tidak overclaim sebagai live model eval.
- Parse success rate: 13/13 (100%), avg token savings: 28.6%
- Rerun suite: **318/318 pass**, tach boundaries OK

### 2026-04-01 - Phase 3 Completion: Polish And Packaging

- Bump version ke 0.3.0 (pyproject.toml + `__init__.py`)
- Update CHANGELOG.md dengan semua fitur 0.3.0
- CLI polish: tambah `--version` / `-V` flag, perbaiki help text semua command
- Dockerfile hardened: multi-stage build, non-root user, health check, CLI entrypoint
- docker-compose update: override entrypoint untuk API mode
- README update: tambah deep analysis features, `analysis/` dir di artifact tree, `--version`
- Rerun suite: **313/313 pass**, tach boundaries OK

### 2026-04-01 - Deep Analysis Layer And Pipeline Integration

- Implementasi 4 modul analisis baru:
  - **CFG Builder**: intra-program control flow graph dengan basic blocks, branch/perform/fallthrough edges
  - **Reference Indexer**: field-level read/write/condition/call_param classification per statement
  - **Data Flow Analyzer**: directed field-to-field data flow graph (MOVE, COMPUTE, READ INTO, WRITE FROM, CALL USING)
  - **Dead Code Detector**: unreachable paragraphs (BFS reachability), unused data items, trivially dead branches
- Tambah contracts: `cfg_output.py`, `data_flow_output.py`, `dead_code_output.py`, `reference_output.py`
- Tambah `analysis` field di `ArtifactIndex` manifest untuk track artifacts analisis baru
- Integrasi ke `pipeline.py`: setiap program yang berhasil di-parse sekarang menghasilkan
  reference index, CFG, data flow graph (JSON + Mermaid), dan dead code report
- Integrasi ke doc generator: program docs sekarang include data flow diagram dan dead code findings
- Integrasi ke doc service: load analysis artifacts dari completed run untuk docs generation
- Update integration test untuk verifikasi analysis artifacts ditulis ke disk
- Tambah 57 tests baru (unit + contract) untuk 4 modul analisis
- Rerun suite: **313/313 pass**, tach boundaries OK

---

### 2026-04-03 - Trust Hardening And CI Hygiene

- Trust hardening: contract drift CLI/API/service, run metrics both paths,
  exponential backoff + jitter, cache key with tool_version + analysis_hash,
  parallel backend clone pattern, lint baseline bersih.
- CI diperkuat: coverage gate 85%, lint sekarang termasuk `tools/`,
  coverage config exclude `antlr_gen/`.
- Docs hygiene: PROGRESS.md test count diupdate ke 326, ADR-013 checklist
  ditandai selesai (implementasi sudah cukup).
- Rerun suite: **326/326 pass**, 91% coverage, ruff clean, tach OK

---

### 2026-04-03 - Fine-Tuning And PyPI Release

- Fine-tuning berhasil: QLoRA CodeLlama-7B pada Colab T4, 3 epochs,
  ~80 training samples dari 14 COBOL programs.
- Model dipublish ke HuggingFace: `WwzFwz/cobol-explain-7b`
- Package dipublish ke PyPI: v0.3.0 (initial), v0.3.1 (dialect + fine-tuning)
- Dialect expansion: `PERFORM THRU` dan `EXEC CICS` ditambahkan ke parser
- Colab notebook ditambahkan untuk reproducible fine-tuning
- Rerun suite: **331/331 pass**, 91% coverage, ruff clean, tach OK

---

## Blockers And Open Questions

- Semua item Phase 0-4 sudah selesai
- Extended `EXEC SQL` dan `SEARCH/SEARCH ALL` dialect masih bisa ditambah nanti
- Sanity test fine-tuned model belum jalan karena OOM di Colab (perlu session baru)

---

## Resources Yang Berguna

- `tests/corpus/test_parser_poc.py` sebagai baseline Lark PoC
- `tests/corpus/test_antlr4_poc.py` sebagai baseline ANTLR4 PoC
- `tests/unit/test_call_graph.py` untuk graph extraction
- `tests/unit/test_rules_extractor.py` untuk business rules extraction
- `tests/integration/test_service_pipeline.py` untuk artifact pipeline end-to-end
