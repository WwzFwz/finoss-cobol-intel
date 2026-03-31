# Progress Tracker

Log pengerjaan project. Update setiap sesi kerja.

---

## Status Saat Ini

**Fase**: 0 — Fondasi
**Mulai**: 2026-03-31
**Target MVP**: -

---

## Checklist Per Fase

### Fase 0 — Fondasi
- [ ] Setup project structure (folders, `pyproject.toml`, `README.md`)
- [ ] Setup virtual environment & dependency management
- [ ] Kumpulkan dan kategorisasi dataset COBOL sample
- [ ] Riset COBOL grammar yang tersedia (lark vs ANTLR4)
- [ ] Buat 5+ test cases COBOL dari sederhana ke kompleks
- [ ] Pilih dan lock down grammar approach
- [ ] Basic parser: bisa parse IDENTIFICATION & DATA DIVISION

### Fase 1 — Static Analysis Core
- [ ] Parser lengkap: semua division dan section utama
- [ ] Handle fixed-format kolom
- [ ] COPYBOOK resolver
- [ ] CALL graph builder (static calls)
- [ ] Business rules extractor: IF/EVALUATE conditions
- [ ] Dependency graph output (JSON + Mermaid)
- [ ] Unit tests untuk semua modul

### Fase 2 — LLM Integration
- [ ] `LLMBackend` abstract interface
- [ ] Claude API backend
- [ ] Ollama backend
- [ ] Context builder (AST → LLM prompt)
- [ ] Smart chunker untuk program besar
- [ ] Explanation engine (technical mode)
- [ ] Explanation engine (business mode)

### Fase 3 — Output & Polish
- [ ] Documentation generator (Markdown)
- [ ] HTML report generator
- [ ] Change impact analyzer
- [ ] CLI interface lengkap
- [ ] README yang bagus dengan demo GIF
- [ ] Docker image

### Fase 4 — Advanced
- [ ] Benchmark: preprocessing vs raw LLM
- [ ] Fine-tune model 7B untuk COBOL
- [ ] Publish model ke HuggingFace
- [ ] Publish ke PyPI

---

## Session Log

### 2026-03-31
- Diskusi konsep, problem statement, dan arsitektur
- Dibuat: `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/RESEARCH.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`
- Next: Setup project structure dan mulai riset grammar COBOL

---

## Blockers & Open Questions

*(Tulis di sini kalau ada yang mentok)*

---

## Resources yang Berguna (ditemukan selama development)

*(Tulis link, library, paper yang ditemukan dan berguna)*
