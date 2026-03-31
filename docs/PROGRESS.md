# Progress Tracker

Log pengerjaan project. Update setiap sesi kerja.

---

## Status Saat Ini

**Fase**: 2 - LLM Integration (ready to start)
**Mulai**: 2026-03-31
**Target MVP**: -
**Test Status**: 134/134 pass

Catatan:

- Fase 0 gate items sudah selesai: parser comparison, ADR-006 parser decision,
  run_id ADR-014, dan AST contract awal.
- Fase 1 sudah selesai: parser hardening, circular `COPY` detection, corpus 10
  sample, regression baseline, artifact writer, dan CLI analyze/graph sudah jalan.
- Repo siap masuk Fase 2 untuk `llm/`, context builder, dan explanation engine.
- Coverage parser juga sudah diperluas untuk subset enterprise yang lebih dekat
  ke finance workloads: `EXEC SQL`, file I/O statements, `COPY ... REPLACING`,
  `PROCEDURE DIVISION USING`, `UNSTRING`, dan `INSPECT`.

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

- [ ] Implementasikan error handling end-to-end sesuai ADR-013
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

- [ ] `LLMBackend` abstract interface di `llm/`
- [ ] `ClaudeBackend` implementation
- [ ] `OllamaBackend` implementation
- [ ] Context builder: AST + rules + graph -> LLM-ready prompt
- [ ] Smart chunker berbasis struktur paragraph/section
- [ ] Explanation engine mode `technical`
- [ ] Explanation engine mode `business`
- [ ] Explanation engine mode `audit`
- [ ] Semua output LLM include traceability ke artifact sumber
- [ ] Evaluation test: raw LLM vs pipeline + LLM pada sample yang sama

---

### Fase 3 - Output And Polish

- [ ] Documentation generator output Markdown per program
- [ ] HTML report generator
- [ ] Change impact analyzer
- [ ] CLI interface lengkap dan terdokumentasi
- [ ] README dengan demo GIF atau video
- [ ] Docker image untuk on-premise deployment
- [ ] `CHANGELOG.md` dan versioning strategy

---

### Fase 4 - Advanced

- [ ] Fine-tune model 7B pada dataset COBOL
- [ ] Benchmark fine-tuned model vs general LLM untuk COBOL task
- [ ] Publish model ke HuggingFace
- [ ] Publish package ke PyPI
- [ ] Read-only API prototype setelah service layer stabil

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

---

## Blockers And Open Questions

- Error handling ADR-013 baru lengkap setelah service layer menangani partial
  failures lebih detail
- Fase 2 belum dimulai: `llm/` backends, context builder, dan explanation engine

---

## Resources Yang Berguna

- `tests/corpus/test_parser_poc.py` sebagai baseline Lark PoC
- `tests/corpus/test_antlr4_poc.py` sebagai baseline ANTLR4 PoC
- `tests/unit/test_call_graph.py` untuk graph extraction
- `tests/unit/test_rules_extractor.py` untuk business rules extraction
- `tests/integration/test_service_pipeline.py` untuk artifact pipeline end-to-end
