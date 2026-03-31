# COBOL Intelligence Platform — Project Plan

## Vision

Open-source platform yang memungkinkan perusahaan fintech dan bank memahami,
mendokumentasikan, dan mempersiapkan migrasi sistem COBOL legacy mereka —
menggunakan kombinasi static analysis dan LLM, yang bisa berjalan sepenuhnya
on-premise tanpa mengirim kode ke server eksternal.

---

## Problem Statement

Bank dan fintech dengan sistem COBOL legacy menghadapi tiga masalah utama:

1. **Knowledge loss** — Developer COBOL pensiun, tidak ada dokumentasi, tidak ada yang mengerti sistem sendiri
2. **Fear of change** — Tidak ada yang tahu dampak perubahan kecil sekalipun
3. **Regulatory pressure** — Regulator minta penjelasan sistem, bank tidak bisa jawab cepat

Solusi existing (IBM tools, konsultan) mahal dan tidak accessible. Tidak ada
open-source tool yang solve ini dengan benar.

---

## Core Principle

> LLM hanya sebaik input yang diterimanya.
> Project ini adalah infrastructure layer yang membuat input itu benar sebelum LLM menyentuhnya.

---

## Modul Utama

### Modul 1 — COBOL Parser & AST Builder
**Tujuan**: Pahami struktur COBOL secara programatik, bukan tebak-tebakan

Input: File `.cbl`, `.cob`, `.cobol`
Output: Abstract Syntax Tree (AST) terstruktur dalam JSON

Yang harus di-handle:
- IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE DIVISION
- WORKING-STORAGE SECTION, FILE SECTION, LINKAGE SECTION
- Tipe data COBOL: PIC, COMP, COMP-3, COMP-5
- OCCURS, REDEFINES, FILLER
- Fixed-format vs free-format COBOL

Tools: `lark` atau `antlr4` dengan COBOL grammar

---

### Modul 2 — COPYBOOK & Dependency Resolver
**Tujuan**: Resolve semua external dependency sebelum analisis

Input: AST + direktori COPYBOOK
Output: AST yang sudah fully resolved, dependency graph antar file

Yang harus di-handle:
- `COPY` statement resolution
- `CALL` statement mapping (static calls)
- Circular dependency detection
- Missing COPYBOOK warning

---

### Modul 3 — Business Rules Extractor
**Tujuan**: Ekstrak kondisi bisnis dari PROCEDURE DIVISION menjadi format yang bisa dibaca manusia

Input: Resolved AST
Output: Decision table, rule list dalam format JSON dan Markdown

Contoh output:
```
Rule #12: Premium rate berlaku JIKA:
  - Account type = SAVINGS
  - Balance > 10,000
  - Tenure >= 2 years
Source: CALCINT.cbl, line 247-263
```

---

### Modul 4 — Dependency & Call Graph Builder
**Tujuan**: Peta lengkap hubungan antar program

Input: Kumpulan file COBOL dalam satu project
Output: Visual graph (Mermaid/Graphviz), JSON adjacency list

Yang di-visualisasikan:
- CALL antar program
- COPY (shared data structure)
- Shared files (SELECT/ASSIGN)

---

### Modul 5 — LLM Explanation Engine
**Tujuan**: Generate penjelasan bahasa natural yang akurat dari AST yang sudah bersih

Input: Resolved AST + Business Rules + Call Graph (bukan raw COBOL)
Output: Penjelasan plain English, dokumentasi teknis, ringkasan untuk bisnis

Mode:
- `--mode technical` — untuk developer
- `--mode business` — untuk CFO/regulator
- `--mode audit` — format untuk kebutuhan compliance

Model yang didukung (pluggable):
- Claude API / OpenAI API (untuk development & testing)
- Ollama + CodeLlama (local, tanpa internet)
- Fine-tuned COBOL model (target jangka panjang)

---

### Modul 6 — Documentation Generator
**Tujuan**: Auto-generate dokumentasi lengkap dari codebase COBOL

Output per program:
- Deskripsi fungsi
- Data dictionary (setiap field dan artinya)
- Input/output specification
- Business rules yang ditemukan
- Dependency list
- Flow diagram (Mermaid)

Output format: Markdown, HTML, JSON

---

### Modul 7 — Change Impact Analyzer
**Tujuan**: Jawab pertanyaan "kalau saya ubah X, apa yang terpengaruh?"

Input: Field name / kondisi / program name + full codebase graph
Output: Daftar program, rule, dan field yang terpengaruh beserta risk level

---

## Arsitektur Sistem

```
CLI / API Layer
      │
      ▼
Orchestration Engine
      │
 ┌────┴─────────────────────┐
 │                          │
 ▼                          ▼
Static Analysis          LLM Layer
Pipeline                 (pluggable)
 │                          │
 ├── Parser (AST)           ├── Claude API
 ├── Resolver (COPYBOOK)    ├── OpenAI API
 ├── Graph Builder          ├── Ollama (local)
 └── Rules Extractor        └── Fine-tuned model
         │                          │
         └──────────┬───────────────┘
                    ▼
           Output Generator
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Markdown        JSON          Graph
  (docs)        (API/int.)    (visual)
```

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Language | Python 3.11+ |
| COBOL Parser | `lark` + custom COBOL grammar |
| Graph | `networkx` + `graphviz` / Mermaid |
| LLM Interface | `anthropic`, `openai`, `ollama` |
| CLI | `click` atau `typer` |
| Output | Markdown, JSON, HTML |
| Testing | `pytest` + COBOL sample programs |
| Packaging | `pip` installable, Docker image |

---

## Fase Pengembangan

### Fase 0 — Fondasi (Minggu 1-2)
- [ ] Setup project structure & environment
- [ ] Kumpulkan dataset: COBOL samples dari Open Mainframe Project & IBM GitHub
- [ ] Buat COBOL grammar untuk parser
- [ ] Basic AST output untuk program sederhana

### Fase 1 — Static Analysis Core (Minggu 3-5)
- [ ] COPYBOOK resolver
- [ ] Call graph builder
- [ ] Business rules extractor (kondisi IF/EVALUATE)
- [ ] Basic dependency graph visualization

### Fase 2 — LLM Integration (Minggu 6-8)
- [ ] Context builder dari AST → LLM-ready prompt
- [ ] Smart chunking untuk program besar
- [ ] Pluggable model interface
- [ ] Explanation engine (technical & business mode)

### Fase 3 — Documentation & Output (Minggu 9-10)
- [ ] Documentation generator (Markdown output)
- [ ] Change impact analyzer
- [ ] HTML report generator
- [ ] CLI polishing

### Fase 4 — Quality & Fine-tuning (Minggu 11-12+)
- [ ] Benchmark accuracy vs raw LLM API
- [ ] Fine-tune model kecil (7B) khusus COBOL
- [ ] Docker image untuk on-premise deployment
- [ ] Comprehensive test suite

---

## Metrik Keberhasilan

- Accuracy business rules extraction vs manual review
- Waktu analisis per 1000 baris COBOL
- Jumlah token yang dihemat vs kirim raw ke API
- Kemampuan handle COPYBOOK dan nested CALL chains
- Bisa jalan fully offline dengan local model

---

## Dataset untuk Development & Testing

- [Open Mainframe Project — COBOL Programming Course](https://github.com/openmainframeproject/cobol-programming-course)
- [IBM COBOL Samples](https://github.com/IBM/IBM-Z-zOS)
- [Rosetta Code — COBOL](https://rosettacode.org/wiki/Category:COBOL)
- COBOL programs dari academic papers (banyak tersedia publik)
