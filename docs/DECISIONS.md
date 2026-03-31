# Architecture Decision Records (ADR)

Setiap keputusan teknis penting dicatat di sini beserta alasannya.
Ini penting untuk project besar supaya tidak lupa kenapa sesuatu dibuat seperti itu.

Format setiap entry:

- **Status**: Proposed / Accepted / Deprecated
- **Context**: Situasi yang memaksa keputusan ini
- **Decision**: Apa yang diputuskan
- **Consequences**: Dampak positif dan negatifnya

---

## ADR-001: Python Sebagai Primary Language

**Status**: Accepted

**Context**: Perlu memilih bahasa untuk membangun seluruh pipeline.

**Decision**: Python 3.11+

**Consequences**:

- (+) Ekosistem terlengkap untuk LLM integration
- (+) `lark`, `antlr4-python3-runtime`, dan tooling data mudah dipakai
- (+) Familiar di komunitas data science / ML
- (+) Mudah untuk packaging dan distribusi
- (-) Lebih lambat dari Go/Rust untuk parsing intensif
- (-) GIL bisa jadi bottleneck untuk parallelism tertentu

---

## ADR-002: Static Analysis Sebelum LLM

**Status**: Accepted

**Context**: Secara teknis bisa saja langsung mengirim COBOL ke LLM dan meminta penjelasan.

**Decision**: Selalu jalankan static analysis pipeline dulu, baru LLM menerima
output yang sudah terstruktur.

**Consequences**:

- (+) LLM mendapat input yang lebih bersih
- (+) Akurasi penjelasan dan ekstraksi rule lebih tinggi
- (+) Hemat token karena tidak mengirim seluruh raw COBOL
- (+) Pipeline tetap berguna walaupun backend LLM tidak tersedia
- (-) Arsitektur lebih kompleks
- (-) Parser harus cukup robust untuk berbagai dialect COBOL

---

## ADR-003: Pluggable LLM Backend

**Status**: Accepted

**Context**: Pengguna enterprise sering tidak bisa mengirim source code ke cloud,
sementara developer individual ingin setup yang cepat.

**Decision**: Gunakan abstraksi backend LLM yang pluggable.

Implementasi target:

- OpenAI API
- Claude API
- Ollama
- Local model backend

**Consequences**:

- (+) Bank bisa pakai fully on-premise dengan local model
- (+) Developer bisa pakai API untuk iterasi cepat
- (+) Fine-tuned model bisa ditambahkan nanti
- (-) Perlu maintain beberapa backend implementation
- (-) Testing jadi lebih kompleks

---

## ADR-004: CLI-First, GUI Later

**Status**: Accepted

**Context**: Web UI memang lebih menarik untuk demo, tetapi terlalu cepat
membangunnya berisiko mendorong arsitektur yang belum matang.

**Decision**: Fokus ke CLI dan artifact output lebih dulu. GUI datang belakangan
setelah service layer dan output contract stabil.

**Consequences**:

- (+) Value lebih cepat untuk developer
- (+) Lebih mudah diintegrasikan ke script dan CI/CD
- (+) Lebih mudah diuji
- (+) GUI nanti punya fondasi yang lebih stabil
- (-) Demo awal kurang visual untuk non-technical audience
- Mitigasi: hasil HTML report dan Mermaid bisa dipakai untuk demo awal

---

## ADR-005: Output Format Utama

**Status**: Accepted

**Context**: Perlu format output yang berguna untuk berbagai use case.

**Decision**:

- **JSON** untuk integrasi programatik dan regression testing
- **Markdown** untuk dokumentasi yang bisa dirender di GitHub atau wiki
- **HTML** untuk report stakeholder non-teknis
- **Mermaid** untuk diagram yang bisa di-embed di Markdown

**Consequences**:

- (+) Fleksibel untuk banyak kebutuhan
- (+) JSON menjadi base contract lintas interface
- (+) Markdown bisa langsung dipush ke repo sebagai docs
- (-) Perlu generator untuk beberapa format output

---

## ADR-006: Parser Default — ANTLR4

**Status**: Accepted (2026-03-31)

**Context**: Parser adalah fondasi project, tetapi memilih parser hanya dari
preferensi library terlalu berisiko. Fase 0 membuat PoC menggunakan `lark`
(Earley) dan `ANTLR4` pada 5 sample COBOL nyata (fixed-format, free-format,
COPY, COMP-3, REDEFINES, OCCURS, CALL, EVALUATE, PERFORM VARYING, array access).

Kedua parser berhasil parse semua 5 sample — 32/32 test lark, 27/27 test ANTLR4.

**Decision**: **ANTLR4 sebagai parser default.** Lark tetap tersedia sebagai
fallback dan untuk quick prototyping.

Alasan utama:

1. Keyword/identifier priority diselesaikan secara natural oleh lexer rule
   ordering — tidak perlu workaround priority annotations seperti di lark
2. Community COBOL85 grammar tersedia di `antlr/grammars-v4` sebagai upgrade path
3. Strongly-typed visitor pattern lebih maintainable untuk project besar
4. Tooling dan debugging ecosystem lebih mature

Mitigasi risiko Java dependency:

- Generated Python files di-commit ke repo
- Contributor hanya butuh Java kalau mengubah grammar
- End user tidak perlu Java sama sekali

Evaluasi lengkap: `docs/PARSER_EVALUATION.md`

**Consequences**:

- (+) Keputusan parser berbasis bukti dari PoC nyata, bukan tebakan
- (+) Natural keyword priority tanpa manual annotations
- (+) Community grammar COBOL85 tersedia untuk scaling ke dialect nyata
- (+) Strongly-typed context objects dan visitor pattern
- (+) Lark tetap tersedia sebagai fallback
- (-) Butuh Java untuk regenerate parser saat grammar berubah
- (-) Generated code (~3000 baris) harus di-commit ke repo

---

## ADR-007: Versioned Contracts Untuk Semua Artifact JSON

**Status**: Accepted

**Context**: Tanpa output contract yang stabil, CLI, API, GUI, dan integrasi
eksternal akan mudah rusak saat shape JSON berubah.

**Decision**: Semua artifact JSON harus didefinisikan di `contracts/` dan wajib
memiliki `schema_version`.

Artifact minimal untuk MVP:

- `manifest.json`
- AST output
- dependency graph output
- business rules output

**Consequences**:

- (+) Integrasi lebih aman
- (+) Contract test bisa ditulis sejak awal
- (+) API dan GUI nanti punya bahasa bersama
- (-) Perubahan output menjadi lebih disiplin dan sedikit lebih lambat

---

## ADR-008: File-System Artifact Store Sebelum Database Persistence

**Status**: Accepted

**Context**: Project butuh model run dan artifact yang rapi, tetapi persistence
enterprise penuh masih premature untuk MVP.

**Decision**: Simpan hasil analisis dalam artifact directory yang stabil di
filesystem. Jangan bangun database persistence penuh di fase awal.

Contoh layout:

```text
artifacts/<project_slug>/<run_id>/
```

**Consequences**:

- (+) Sederhana untuk MVP
- (+) Mudah diinspeksi manual
- (+) Nanti bisa dipetakan ke object storage atau DB
- (-) Belum optimal untuk multi-user dan query kompleks

---

## ADR-009: Package Boundaries Harus Dikunci Sebelum Coding

**Status**: Accepted

**Context**: Tanpa boundary yang jelas, CLI, parser, formatter, dan LLM layer
akan mudah saling menempel dan sulit direfactor saat API atau GUI ditambahkan.

**Decision**: Kunci package layout berikut sejak awal:

```text
src/cobol_intel/
  core/
  contracts/
  parsers/
  analysis/
  llm/
  outputs/
  service/
  cli/
```

Rules:

- `cli` tidak menyimpan business logic
- `analysis` tidak bergantung pada backend LLM
- `contracts` menjadi bahasa bersama lintas layer
- interface baru nanti masuk lewat `service`

**Consequences**:

- (+) Refactor di masa depan lebih murah
- (+) GUI dan API nanti lebih mudah ditambahkan
- (+) Testing bisa difokuskan per layer
- (-) Perlu disiplin boundary sejak awal

---

## ADR-010: Testing Strategy Harus Berbasis Corpus, Contract, Dan Regression

**Status**: Accepted

**Context**: Menulis "akan ada benchmark dan test suite" terlalu vague untuk
project parser-heavy seperti ini.

**Decision**: Testing dibagi menjadi empat lapisan:

1. corpus tests untuk parser dan dialect coverage
2. contract tests untuk JSON schema
3. regression tests untuk expected artifact
4. evaluation tests untuk membandingkan raw LLM vs preprocessing pipeline

**Consequences**:

- (+) Risiko regression parser lebih cepat terdeteksi
- (+) Output contract tetap stabil
- (+) LLM dibuktikan sebagai enhancer, bukan fondasi tunggal
- (-) Butuh effort dataset dan maintenance fixture

---

## ADR-011: API Ditunda Sampai Service Layer Dan Contract Stabil

**Status**: Accepted

**Context**: Ada kebutuhan integrasi ke sistem lain, tetapi membangun API terlalu
cepat bisa menghasilkan endpoint yang langsung obsolete setelah contract berubah.

**Decision**: API bukan prioritas fase awal. Tambahkan read-only API prototype
setelah service layer dan artifact contract stabil.

**Consequences**:

- (+) Backend tidak dikunci terlalu cepat oleh desain API
- (+) Kontrak lebih matang saat API diperkenalkan
- (+) GUI nanti bisa dibangun di atas interface yang lebih sehat
- (-) Integrasi via HTTP belum tersedia di MVP paling awal

---

## ADR-013: Error Handling Strategy — Partial Artifact Dengan Warnings

**Status**: Accepted

**Context**: COBOL codebase di bank nyata tidak pernah 100% bersih. Selalu ada
file dengan dialect tidak standar, COPYBOOK yang hilang, atau syntax edge case
yang tidak di-handle parser. Belum ada keputusan eksplisit tentang apa yang
terjadi saat pipeline gagal di sebagian file.

Tanpa keputusan ini, implementer akan membuat pilihan secara tidak sadar dan
hasilnya tidak konsisten antar modul.

**Decision**: Pipeline menggunakan strategi **partial artifact dengan warnings**,
bukan fail-fast.

Aturannya:

- Jika satu file gagal di-parse, file itu dicatat di `manifest.json` bagian
  `errors`, pipeline tetap lanjut ke file berikutnya.
- Artifact yang berhasil tetap ditulis ke filesystem.
- `manifest.json` mendapat status `partially_completed` jika ada error, bukan
  `completed`.
- Jika **semua** file gagal, status menjadi `failed`.
- Setiap error harus menyertakan: file path, modul yang gagal, pesan error,
  dan jika bisa — baris yang bermasalah.

Contoh manifest dengan partial failure:

```json
{
  "schema_version": "1.0",
  "run_id": "run_20260331_001",
  "status": "partially_completed",
  "artifacts": {
    "ast": ["ast/CALCINT.json", "ast/PAYREC.json"]
  },
  "warnings": [
    "COPYBOOK 'CUSTMAST' tidak ditemukan, field dari COPYBOOK ini tidak di-resolve"
  ],
  "errors": [
    {
      "file": "LEGACY01.cbl",
      "module": "parser",
      "message": "Unexpected token di baris 342: EXEC CICS — dialect CICS belum didukung",
      "line": 342
    }
  ]
}
```

**Fail-fast hanya berlaku** untuk kondisi yang menunjukkan setup yang salah,
bukan konten COBOL yang bermasalah. Contoh: direktori input tidak ada, backend
LLM tidak bisa dihubungi dan mode LLM wajib diaktifkan.

**Consequences**:

- (+) Tool tetap berguna walaupun sebagian file tidak bisa diproses
- (+) User tahu persis file mana yang bermasalah dan kenapa
- (+) Partial artifact tetap bisa dipakai untuk file yang berhasil
- (+) Konsisten antar modul — semua ikut aturan yang sama
- (-) Implementasi lebih kompleks dari sekadar raise exception
- (-) User perlu selalu cek `manifest.json` dan tidak bisa asumsikan run = sukses

---

## ADR-012: Enterprise Auth Dan RBAC Bukan Scope MVP

**Status**: Accepted

**Context**: Auth, RBAC, dan audit platform memang penting untuk enterprise,
tetapi belum perlu dibangun pada fase open-source MVP.

**Decision**: Fitur-fitur tersebut ditunda. Arsitektur hanya perlu memastikan
bahwa penambahannya nanti tidak terhalang.

**Consequences**:

- (+) Fokus tim tetap pada parser, contracts, dan pipeline inti
- (+) MVP lebih cepat selesai
- (-) Belum siap langsung menjadi multi-user enterprise platform

---

## ADR-014: Run ID Format — Timestamp + Random Suffix

**Status**: Accepted (2026-03-31)

**Context**: Artifact directory layout menggunakan `run_id` sebagai nama folder
(`artifacts/<project>/<run_id>/`). Format belum diputuskan — opsi utama adalah
UUID v4 atau timestamp-based.

**Decision**: Format `run_YYYYMMDD_HHMMSS_XXXX` dimana:

- Timestamp dalam UTC
- `XXXX` adalah 4-char hex random suffix untuk uniqueness dalam detik yang sama

Contoh: `run_20260331_143052_a7f3`

**Consequences**:

- (+) Human-readable — mudah diinspeksi di filesystem dan log
- (+) Sortable secara natural (ls, sort)
- (+) Cukup unique untuk single-user CLI tool
- (-) Tidak cocok untuk distributed system multi-node (tapi itu bukan scope MVP)
- (-) Tidak sependek UUID v4 untuk embedding di URL nanti

Implementasi: `src/cobol_intel/contracts/run_id.py`
