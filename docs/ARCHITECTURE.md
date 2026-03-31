# Architecture Deep Dive

Dokumen ini menjelaskan keputusan arsitektur dan alasan di baliknya.
Fokus utamanya adalah membuat MVP yang benar-benar bisa dibangun, diuji, dan
diintegrasikan, tanpa terlalu cepat masuk ke kompleksitas enterprise penuh.

---

## Architecture Priorities

Prioritas arsitektur untuk fase awal:

1. Parser dan static analysis harus cukup kuat untuk sample COBOL nyata.
2. Output harus punya contract yang stabil dan versioned.
3. Core pipeline harus berguna walaupun LLM dimatikan.
4. CLI, API, dan GUI nanti harus berbagi fondasi yang sama melalui service dan contracts.

---

## Kenapa Static Analysis Dulu, Bukan Langsung LLM

LLM tanpa preprocessing pada COBOL memiliki masalah fundamental:

| Masalah | Dampak | Solusi di project ini |
|---|---|---|
| COPYBOOK tidak resolved | LLM menebak isi struktur data | Resolver sebelum LLM |
| CALL ke program lain tidak diketahui | Analisis tidak lengkap | Call graph builder |
| Program sangat besar | Melebihi context window | Smart chunking dengan konteks |
| COMP-3 / packed decimal | Sering salah interpretasi | Type-aware AST |
| Variabel tidak deskriptif | LLM sulit infer arti | Enrichment dari context sekitar |

Kesimpulan: **LLM hanya digunakan setelah data sudah bersih dan terstruktur.**

---

## Package Boundaries

Arsitektur package harus menjaga dependency flow tetap sehat:

```text
contracts <- core <- service <- cli
parsers   <- analysis <- service
llm       <- service
outputs   <- service
```

Penjelasan:

- `contracts` berisi schema, manifest, dan DTO yang menjadi bahasa bersama.
- `core` berisi domain abstractions dan orchestration interfaces yang tidak
  bergantung pada UI.
- `parsers` dan `analysis` menghasilkan artifact inti yang bisa dipakai tanpa LLM.
- `service` menggabungkan pipeline, run lifecycle, dan artifact writing.
- `cli` hanyalah lapisan pemanggil.

Implikasi:

- Jika nanti ada API atau GUI, keduanya harus masuk lewat `service`.
- Jangan menaruh logic parsing, graph analysis, atau formatting langsung di CLI.

---

## Canonical Output Contracts

Project ini perlu punya output yang stabil sebelum menambah API atau GUI.

Minimal artifact contract yang harus ada:

- `manifest.json`
- `ast/<program>.json`
- `graphs/dependency_graph.json`
- `rules/business_rules.json`

Semua artifact JSON harus memiliki:

- `schema_version`
- `tool_version`
- `generated_at`

Khusus `manifest.json`, minimal field-nya:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "run_id": "run_20260331_001",
  "project_name": "sample-banking-core",
  "status": "completed",
  "started_at": "2026-03-31T10:00:00Z",
  "finished_at": "2026-03-31T10:00:24Z",
  "input_paths": ["./samples"],
  "artifacts": {
    "ast": ["ast/CALCINT.json"],
    "graphs": ["graphs/dependency_graph.json"],
    "rules": ["rules/business_rules.json"]
  },
  "warnings": [],
  "errors": []
}
```

Tujuan utama contract ini:

- mudah di-parse sistem lain
- bisa dipakai ulang tanpa rerun pipeline
- aman untuk regression testing
- menjadi fondasi API dan GUI nanti

---

## Run Lifecycle Dan Artifact Model

Walaupun persistence penuh ke database ditunda, semua execution harus dianggap
sebagai `analysis run` yang eksplisit.

Lifecycle minimum:

```text
queued -> running -> completed
queued -> running -> failed
```

Setiap run menulis artifact ke filesystem dengan struktur:

```text
artifacts/
`-- <project_slug>/
    `-- <run_id>/
        +-- manifest.json
        +-- ast/
        +-- graphs/
        +-- rules/
        +-- docs/
        `-- logs/
```

Kenapa ini penting:

- CLI bisa menampilkan hasil run terakhir
- API nanti bisa membaca artifact yang sama
- GUI nanti cukup browse manifest dan artifact, tidak perlu coupling langsung ke parser internals
- Storage ini bisa dipindahkan ke object storage atau DB layer nanti tanpa mengubah semantic model

---

## Parser Strategy

Parser adalah fondasi seluruh sistem, jadi keputusan parser tidak boleh diambil
hanya berdasarkan preferensi library.

### Candidate A: Lark

Kelebihan:

- Pure Python
- Mudah diintegrasikan ke codebase
- Fleksibel untuk grammar custom

Risiko:

- Grammar COBOL harus banyak ditulis sendiri
- Bisa lambat atau rapuh untuk dialect yang kompleks

### Candidate B: ANTLR4 COBOL Grammar

Kelebihan:

- Ada grammar yang bisa dijadikan titik awal
- Lebih realistis untuk validasi cepat terhadap COBOL nyata

Risiko:

- Tooling lebih berat
- Grammar komunitas tetap perlu divalidasi dan diadaptasi

### Decision Gate

Fase 0 harus menjalankan PoC kecil pada minimal 3-4 sample COBOL nyata:

- fixed-format sederhana
- free-format sederhana
- sample dengan `COPY`
- sample dengan `COMP-3`, `REDEFINES`, atau `CALL`

Metrik evaluasi awal:

- parse success / fail
- effort implementasi preprocessing
- kualitas tree hasil parse untuk kebutuhan AST internal
- kemudahan debugging saat gagal

Setelah itu baru parser default dikunci.

---

## Smart Chunking Strategy

Untuk program besar yang melebihi context window LLM:

```text
Program COBOL besar
    |
    v
Split per section atau paragraph boundary
    |
    v
Tambahkan envelope per chunk:
  - global data definitions yang relevan
  - summary program secara keseluruhan
  - paragraphs yang dipanggil atau memanggil chunk ini
    |
    v
LLM analisis per chunk dengan konteks cukup
    |
    v
Merge dan deduplicate hasil
```

Prinsip penting:

- Chunking tidak boleh memotong statement secara sembarangan.
- Chunking harus berbasis struktur program, bukan sekadar jumlah token.

---

## Traceability

Salah satu nilai jual utama project ini adalah hasil yang bisa ditelusuri balik
ke source COBOL.

Setiap business rule atau explanation idealnya mengandung:

- file sumber
- paragraph atau section sumber
- range line sumber
- artifact asal, misalnya AST node atau graph edge terkait

Contoh bentuk rule:

```json
{
  "schema_version": "1.0",
  "rule_id": "BR-047",
  "source": {
    "file": "CALCINT.cbl",
    "paragraph": "APPLY-PREMIUM-RATE",
    "lines": "247-263"
  },
  "conditions": [
    {"field": "WS-ACCOUNT-TYPE", "operator": "=", "value": "SAV"},
    {"field": "WS-BALANCE", "operator": ">", "value": 10000}
  ],
  "action": "PERFORM APPLY-PREMIUM-RATE",
  "description": "Premium rate berlaku untuk akun Savings dengan saldo tertentu."
}
```

Tanpa traceability, hasil LLM akan terlihat seperti demo. Dengan traceability,
hasilnya lebih layak dipakai untuk dokumentasi, audit, dan review manusia.

---

## LLM Backend Architecture

Backend model harus pluggable dan tidak mengubah pipeline inti.

```python
class LLMBackend(ABC):
    @abstractmethod
    def explain(self, context: "COBOLContext", mode: "ExplanationMode") -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize_rules(self, rules: list["BusinessRule"], mode: "ExplanationMode") -> str:
        raise NotImplementedError
```

Implementasi target:

- `OpenAIBackend`
- `ClaudeBackend`
- `OllamaBackend`
- `LocalModelBackend`

Catatan:

- Static analysis tidak boleh bergantung pada backend ini.
- Jika tidak ada backend LLM, artifact static analysis harus tetap dihasilkan.

---

## On-Premise Deployment

Untuk bank yang tidak bisa mengirim kode ke cloud, deployment baseline adalah:

```text
Bank Server
  |
  +-- cobol-intel container
  |     +-- parser / resolver / analysis
  |     +-- local artifact storage
  |     `-- optional local LLM via Ollama
  |
  `-- COBOL source stays inside bank environment
```

Yang belum menjadi target MVP:

- multi-tenant isolation
- enterprise auth dan RBAC
- central admin dashboard

Namun arsitektur sengaja dijaga agar fitur-fitur itu bisa ditambahkan nanti di
atas service layer dan contract yang sudah stabil.

---

## GUI Dan API Positioning

### CLI-First

CLI adalah antarmuka pertama karena:

- paling cepat memberi value ke developer
- mudah diintegrasikan ke script dan CI/CD
- paling mudah diuji

### API Later

API layak ditambahkan setelah:

- manifest dan artifact contract stabil
- service layer stabil
- regression test cukup kuat

### GUI Later

GUI berguna untuk demo, stakeholder non-teknis, dan browsing artifact, tetapi:

- tidak boleh datang sebelum contract stabil
- tidak boleh bergantung langsung pada parser internals
- sebaiknya tetap satu repo dulu sampai interface backend matang

---

## Testing Architecture

Testing harus dibagi menjadi beberapa lapisan:

### Parser Corpus Tests

Validasi parser pada sample COBOL lintas sumber dan lintas dialect.

### Contract Tests

Validasi semua output JSON terhadap schema di `contracts/`.

### Regression Tests

Commit expected artifact untuk sample penting agar perubahan parser mudah dideteksi.

### LLM Evaluation

Bandingkan raw LLM vs preprocessing pipeline untuk akurasi, token usage, dan traceability.

---

## Summary

Arsitektur project ini sengaja dioptimalkan untuk urutan berikut:

1. parser yang tervalidasi
2. output contract yang stabil
3. service layer yang reusable
4. LLM yang pluggable
5. API dan GUI sebagai consumer, bukan pusat logika

Dengan urutan ini, project tetap menarik sebagai portfolio AI, tetapi juga
terlihat seperti software yang benar-benar siap diintegrasikan ke lingkungan perusahaan.
