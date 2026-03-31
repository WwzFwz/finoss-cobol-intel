# Architecture Decision Records (ADR)

Setiap keputusan teknis penting dicatat di sini beserta alasannya.
Ini penting untuk project besar supaya tidak lupa kenapa sesuatu dibuat seperti itu.

Format setiap entry:
- **Status**: Proposed / Accepted / Deprecated
- **Context**: Situasi yang memaksa keputusan ini
- **Decision**: Apa yang diputuskan
- **Consequences**: Dampak positif dan negatifnya

---

## ADR-001: Python sebagai Primary Language

**Status**: Accepted

**Context**: Perlu memilih bahasa untuk membangun seluruh pipeline.

**Decision**: Python 3.11+

**Consequences**:
- (+) Ekosistem terlengkap untuk LLM integration (anthropic, openai, huggingface)
- (+) `lark`, `antlr4` tersedia untuk parsing
- (+) Familiar di komunitas data science / ML
- (+) Mudah untuk packaging dan distribusi
- (-) Lebih lambat dari Go/Rust untuk parsing intensif
- (-) GIL bisa jadi bottleneck untuk parallelism

---

## ADR-002: Static Analysis Sebelum LLM, Bukan Langsung LLM

**Status**: Accepted

**Context**: Bisa saja langsung kirim COBOL ke LLM API dan minta penjelasan.

**Decision**: Selalu jalankan static analysis pipeline dulu (parse, resolve, build graph), baru LLM menerima output yang sudah terstruktur.

**Consequences**:
- (+) LLM dapat input yang bersih, akurasi jauh lebih tinggi
- (+) Hemat token (tidak kirim seluruh raw COBOL)
- (+) Bisa jalan tanpa LLM sama sekali untuk fitur static analysis
- (+) LLM bisa diganti tanpa mengubah pipeline
- (-) Lebih kompleks untuk dibangun
- (-) Parser harus robust untuk berbagai dialek COBOL

---

## ADR-003: Pluggable LLM Backend

**Status**: Accepted

**Context**: Pengguna enterprise (bank) tidak bisa kirim kode ke cloud. Pengguna individual mau pakai API yang mudah.

**Decision**: Abstraksi `LLMBackend` interface. Implementasi: Claude API, OpenAI, Ollama (local), fine-tuned model.

**Consequences**:
- (+) Bank bisa pakai fully on-premise dengan Ollama
- (+) Developer bisa pakai API untuk setup cepat
- (+) Fine-tuned model bisa di-plug in nanti
- (-) Perlu maintain multiple backend implementations
- (-) Testing lebih kompleks

---

## ADR-004: CLI-First, Web UI Nanti

**Status**: Accepted

**Context**: Bisa bangun web UI dulu supaya lebih "impressive" untuk demo.

**Decision**: Fokus ke CLI yang solid dulu. Web UI adalah fase berikutnya.

**Consequences**:
- (+) Developer dapat value lebih cepat
- (+) Lebih mudah di-integrate ke CI/CD pipeline bank
- (+) Lebih mudah di-test
- (-) Kurang visual untuk demo ke non-technical audience
- Mitigasi: output HTML report yang bisa dibuka di browser

---

## ADR-005: Output Format

**Status**: Accepted

**Context**: Perlu format output yang berguna untuk berbagai pengguna.

**Decision**:
- **JSON**: untuk integrasi programatik dan tooling lain
- **Markdown**: untuk dokumentasi yang bisa di-render di GitHub/Confluence
- **HTML**: untuk report yang bisa dibagikan ke stakeholder non-teknis
- **Mermaid**: untuk diagram yang embedded di Markdown

**Consequences**:
- (+) Fleksibel untuk berbagai use case
- (+) Markdown bisa langsung di-push ke repo sebagai docs
- (-) Perlu generator untuk setiap format

---

## ADR-006: Lark sebagai COBOL Parser

**Status**: Proposed (perlu validasi)

**Context**: Perlu parser yang bisa handle COBOL grammar yang kompleks.

**Options yang dipertimbangkan**:
1. `lark` — Python, Earley/LALR parser, bisa handle ambiguous grammar
2. `antlr4` — Java-based tapi ada Python runtime, grammar COBOL sudah tersedia
3. GnuCOBOL — C compiler, terlalu kompleks untuk di-embed
4. Custom regex — tidak cukup robust untuk production

**Decision**: Mulai dengan `lark` menggunakan grammar custom. Evaluasi ANTLR4 COBOL grammar sebagai alternatif.

**Consequences**:
- (+) Pure Python, mudah di-maintain
- (+) Earley parser bisa handle grammar yang ambigu
- (-) Grammar COBOL harus ditulis sendiri (effort besar)
- (-) Mungkin lambat untuk file sangat besar
