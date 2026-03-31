# COBOL Intelligence Platform - Project Plan

## Vision

Open-source platform yang memungkinkan perusahaan fintech dan bank memahami,
mendokumentasikan, dan mempersiapkan migrasi sistem COBOL legacy mereka
menggunakan kombinasi static analysis dan LLM, yang bisa berjalan sepenuhnya
on-premise tanpa mengirim kode ke server eksternal.

---

## Problem Statement

Bank dan fintech dengan sistem COBOL legacy menghadapi tiga masalah utama:

1. **Knowledge loss** - Developer COBOL pensiun, dokumentasi minim, dan pengetahuan sistem hilang.
2. **Fear of change** - Tidak ada yang tahu dampak perubahan kecil sekalipun.
3. **Regulatory pressure** - Regulator meminta penjelasan sistem, tetapi bank sulit menjawab cepat.

Solusi existing seperti tools enterprise besar atau konsultan sangat mahal.
Belum ada tool open-source yang benar-benar fokus pada pemahaman dan dokumentasi
COBOL dengan pendekatan yang aman untuk lingkungan regulated.

---

## Core Principle

> LLM hanya sebaik input yang diterimanya.
> Project ini adalah infrastructure layer yang membuat input itu benar sebelum
> LLM menyentuhnya.

---

## MVP Guardrails

Supaya project ini tetap executable dan tidak over-engineered di fase awal:

- Stabilkan **contract output** sebelum membangun banyak fitur.
- Validasi **parser strategy** dengan proof of concept kecil, bukan asumsi.
- Pisahkan **core logic** dari CLI, output formatter, dan backend LLM sejak awal.
- Gunakan **filesystem artifact layout** yang extensible sebelum menambah database.
- Tunda **auth, RBAC, multi-user persistence, dan admin enterprise features**
  sampai ada kebutuhan nyata.

---

## Package Structure

Struktur paket harus dikunci sebelum coding supaya CLI, API, dan GUI nanti bisa
memakai fondasi yang sama.

```text
src/cobol_intel/
+-- core/         # domain models dan orchestration yang bebas dari UI
+-- contracts/    # Pydantic schemas, schema versioning, manifest
+-- parsers/      # COBOL parser, preprocessor, COPYBOOK resolver
+-- analysis/     # graph builder, rules extractor, impact analysis
+-- llm/          # backend adapters: OpenAI, Claude, Ollama, local
+-- outputs/      # markdown/json/html/mermaid generators
+-- service/      # pipeline service, run management, artifact writer
`-- cli/          # command-line entrypoints
```

Aturan boundary:

- `core` dan `contracts` tidak boleh import dari `cli`.
- `analysis` dan `parsers` tidak boleh bergantung pada backend LLM.
- `cli` hanya memanggil `service`, tidak menyimpan business logic.
- GUI atau API nanti harus menjadi consumer dari `service` dan `contracts`,
  bukan mengakses internals secara liar.

---

## Output Contracts And Artifact Layout

Sebelum integrasi API atau GUI dibangun, project ini harus punya kontrak output
yang stabil.

### Contract Principles

- Semua artifact JSON wajib memiliki `schema_version`.
- Semua run wajib memiliki `run_id`, `created_at`, `status`, dan `tool_version`.
- Output harus backward-conscious. Perubahan shape besar harus menaikkan schema version.
- Contract disimpan di `contracts/` dan divalidasi lewat automated tests.

### Job Lifecycle

Minimal lifecycle untuk semua execution:

```text
queued -> running -> completed
queued -> running -> failed
```

Status ini dipakai lebih dulu di CLI manifest dan artifact metadata. Nanti
status yang sama bisa dipakai ulang oleh API dan GUI.

### Artifact Directory Layout

Untuk MVP, persistence penuh ke database belum wajib. Sebagai gantinya, setiap
analysis run ditulis ke filesystem dengan layout yang stabil:

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

`manifest.json` minimal berisi:

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

Layout ini sengaja dipilih supaya nanti mudah dipetakan ke object storage atau
database tanpa mengubah struktur logical artifact.

---

## Modul Utama

### Modul 1 - COBOL Parser And AST Builder

**Tujuan**: Pahami struktur COBOL secara programatik, bukan tebak-tebakan.

Input: file `.cbl`, `.cob`, `.cobol`
Output: Abstract Syntax Tree (AST) terstruktur dalam JSON

Yang harus di-handle:

- IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE DIVISION
- WORKING-STORAGE SECTION, FILE SECTION, LINKAGE SECTION
- Tipe data COBOL: PIC, COMP, COMP-3, COMP-5
- OCCURS, REDEFINES, FILLER
- Fixed-format vs free-format COBOL

Catatan penting:

- Pilihan parser tidak boleh dikunci hanya dari opini.
- Fase 0 harus menjalankan PoC kecil untuk `lark` dan `ANTLR4` pada sample
  COBOL nyata sebelum keputusan akhir dibuat.

---

### Modul 2 - COPYBOOK And Dependency Resolver

**Tujuan**: Resolve semua external dependency sebelum analisis.

Input: AST + direktori COPYBOOK
Output: AST yang sudah fully resolved, dependency graph antar file

Yang harus di-handle:

- `COPY` statement resolution
- `CALL` statement mapping untuk static calls
- Circular dependency detection
- Missing COPYBOOK warning

---

### Modul 3 - Business Rules Extractor

**Tujuan**: Ekstrak kondisi bisnis dari PROCEDURE DIVISION menjadi format yang
bisa dibaca manusia.

Input: resolved AST
Output: decision table dan rule list dalam format JSON dan Markdown

Contoh output:

```text
Rule #12: Premium rate berlaku jika:
  - Account type = SAVINGS
  - Balance > 10,000
  - Tenure >= 2 years
Source: CALCINT.cbl, line 247-263
```

---

### Modul 4 - Dependency And Call Graph Builder

**Tujuan**: Peta lengkap hubungan antar program.

Input: kumpulan file COBOL dalam satu project
Output: visual graph dalam Mermaid/Graphviz dan adjacency list JSON

Yang divisualisasikan:

- `CALL` antar program
- `COPY` untuk shared data structure
- Shared files melalui `SELECT` dan `ASSIGN`

---

### Modul 5 - LLM Explanation Engine

**Tujuan**: Generate penjelasan bahasa natural yang akurat dari AST yang sudah
bersih.

Input: resolved AST + business rules + call graph, bukan raw COBOL
Output: penjelasan plain English, dokumentasi teknis, dan ringkasan untuk bisnis

Mode:

- `--mode technical` untuk developer
- `--mode business` untuk stakeholder non-teknis
- `--mode audit` untuk kebutuhan compliance

Model yang didukung secara pluggable:

- Claude API / OpenAI API untuk development dan testing
- Ollama + local model untuk lingkungan on-premise
- Fine-tuned COBOL model sebagai target jangka panjang

Catatan MVP:

- LLM tidak wajib untuk semua command.
- Static analysis pipeline harus tetap berguna walaupun backend LLM tidak tersedia.
- Semua output LLM harus bisa ditrace ke artifact static analysis yang menjadi sumbernya.

---

### Modul 6 - Documentation Generator

**Tujuan**: Auto-generate dokumentasi lengkap dari codebase COBOL.

Output per program:

- Deskripsi fungsi
- Data dictionary untuk setiap field
- Input/output specification
- Business rules yang ditemukan
- Dependency list
- Flow diagram dalam Mermaid

Output format: Markdown, HTML, JSON

---

### Modul 7 - Change Impact Analyzer

**Tujuan**: Jawab pertanyaan "kalau saya ubah X, apa yang terpengaruh?"

Input: field name, kondisi, atau program name + full codebase graph
Output: daftar program, rule, dan field yang terpengaruh beserta risk level

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

Project ini didesain supaya integrasi perusahaan bisa dilakukan bertahap tanpa
memaksa kita membangun full platform sejak hari pertama.

Prinsip integrasi:

- CLI adalah **client pertama** dari service layer, bukan pusat business logic.
- Kontrak utama untuk integrasi awal adalah **JSON artifact + manifest**, bukan web dashboard.
- API layer boleh ditambahkan setelah contract output dan service layer stabil.
- GUI adalah consumer opsional dan tidak boleh mendikte desain core pipeline.

### GUI Strategy

GUI boleh dibuat nanti, tetapi:

- Bukan prioritas Fase 0 atau Fase 1
- Sebaiknya tetap satu repo dulu sampai `contracts` dan `service` stabil
- Jika suatu saat dipisah repo, GUI harus mengonsumsi contract yang versioned,
  bukan mengimpor internal module secara langsung

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Language | Python 3.11+ |
| COBOL Parser | `lark` atau `antlr4-python3-runtime` |
| Graph | `networkx` + `graphviz` / Mermaid |
| LLM Interface | `anthropic`, `openai`, `ollama` |
| Contract Validation | `pydantic` |
| CLI | `click` atau `typer` |
| Output | Markdown, JSON, HTML |
| Testing | `pytest` + corpus COBOL sample |
| Packaging | `pip` installable, Docker image |

---

## Fase Pengembangan

### Fase 0 - Fondasi (Minggu 1-2)

- [x] Setup project structure dan environment
- [x] Kunci package structure: `core`, `contracts`, `parsers`, `analysis`,
      `llm`, `outputs`, `service`, `cli`
- [x] Definisikan schema output awal: `manifest`, `ast`, `dependency_graph`,
      `business_rules`
- [x] Tentukan versioning strategy untuk semua artifact JSON (`schema_version`)
- [x] Tentukan artifact directory layout untuk setiap analysis run
- [x] Kumpulkan dataset COBOL sample dari Open Mainframe Project, IBM, Rosetta,
      dan sample fixed-format
- [x] Buat corpus parser awal: minimal 3-4 sample COBOL realistis dari sumber berbeda
- [x] Buat PoC parser dengan `lark`
- [x] Buat PoC parser dengan `ANTLR4` COBOL grammar
- [x] Bandingkan hasil PoC dan lock parser approach
- [x] Basic AST output untuk program sederhana
- [x] Manifest run pertama yang valid terhadap schema

### Fase 1 - Static Analysis Core (Minggu 3-5)

- [x] Parser lengkap untuk division dan section utama
- [x] Handle fixed-format preprocessing
- [x] COPYBOOK resolver
- [x] Deteksi circular dependency antar COPYBOOK
- [x] Call graph builder
- [x] Business rules extractor untuk kondisi `IF` dan `EVALUATE`
- [x] Basic dependency graph visualization
- [x] JSON artifact writer yang konsisten ke artifact directory
- [x] Contract tests untuk semua output JSON
- [x] Corpus test suite: minimal 10 program COBOL
- [x] Regression tests untuk sample corpus

### Fase 2 - LLM Integration (Minggu 6-8)

- [x] `service` orchestration untuk menjalankan pipeline end-to-end
- [x] Context builder dari AST ke prompt yang siap untuk LLM
- [x] Smart chunking untuk program besar
- [x] Pluggable model interface
- [x] Explanation engine untuk technical mode
- [x] Explanation engine untuk business mode
- [x] Traceability: output LLM menunjuk ke source artifact dan lokasi program

### Fase 3 - Output, Governance, And Integration (Minggu 9-10)

- [x] Audit/event log artifact (`logs/audit_events.jsonl`) untuk analysis dan explain runs
- [x] Governance summary pada `manifest.json` untuk sensitivity, deployment tier, dan token usage
- [x] Approved model registry + preset helpers untuk backend LLM
- [x] Sensitivity classification helper untuk artifact COBOL
- [x] Redaction helper untuk prompt cloud pada workload sensitif
- [ ] Retry / timeout / fallback policy per backend
- [ ] Token budget / quota policy
- [ ] Documentation generator untuk Markdown
- [ ] Change impact analyzer
- [ ] HTML report generator
- [ ] CLI polishing
- [ ] Optional read-only API prototype untuk consume artifact
- [ ] Output directory dan artifact browsing yang lebih rapi
- [ ] Finalisasi layout agar siap dikonsumsi GUI nanti

### Fase 4 - Quality And Fine-Tuning (Minggu 11-12+)

- [ ] Benchmark accuracy vs raw LLM API
- [ ] Fine-tune model kecil khusus COBOL
- [ ] Docker image untuk on-premise deployment
- [ ] Comprehensive test suite

---

## Metrik Keberhasilan

- Parse success rate pada corpus sample lintas sumber
- Accuracy business rules extraction vs manual review
- Waktu analisis per 1000 baris COBOL
- Jumlah token yang dihemat vs mengirim raw COBOL ke API
- Kemampuan handle COPYBOOK dan nested call chains
- Bisa jalan fully offline dengan local model
- Semua artifact JSON valid terhadap schema version yang aktif
- Output run bisa dikonsumsi ulang tanpa menjalankan parser lagi

---

## Testing Strategy

Testing plan untuk MVP harus konkret dan otomatis.

### 1. Dialect Corpus Tests

- Minimal 10 program COBOL dari beberapa sumber: IBM, Open Mainframe Project,
  Rosetta Code, dan sample fixed-format
- Parser harus diuji pada variasi fixed-format, free-format, `COPY`, `CALL`,
  `COMP-3`, `REDEFINES`, dan `OCCURS`
- Setiap sample diberi label capability apa saja yang di-cover

### 2. Contract Tests

- Setiap artifact JSON harus lolos validasi schema di `contracts/`
- `manifest.json` wajib selalu valid walaupun run gagal
- Perubahan shape output tanpa update schema harus dianggap gagal

### 3. Regression Tests

- Untuk sample program utama, expected output di-commit ke repo
- Jika AST, rules, atau graph berubah, test harus memperlihatkan diff yang jelas
- Regression test dipakai untuk mencegah refactor parser merusak output lama

### 4. LLM Evaluation Tests

- Bandingkan output raw LLM vs output dengan preprocessing
- Ukur akurasi, token usage, dan traceability
- LLM test tidak boleh menjadi satu-satunya bukti bahwa pipeline bekerja

---

## Out Of Scope Untuk MVP

Hal-hal ini penting, tetapi tidak perlu dibangun sekarang:

- Multi-user project persistence penuh
- RBAC dan auth enterprise
- Full auth, RBAC, dan approval workflow tingkat platform
- GUI interaktif penuh
- Fine-tuned model produksi
- Dynamic `CALL` resolution yang sempurna untuk semua kasus

---

## Dataset Untuk Development And Testing

- [Open Mainframe Project - COBOL Programming Course](https://github.com/openmainframeproject/cobol-programming-course)
- [IBM COBOL Samples](https://github.com/IBM/IBM-Z-zOS)
- [Rosetta Code - COBOL](https://rosettacode.org/wiki/Category:COBOL)
- COBOL programs dari academic papers yang tersedia publik
