# Parser PoC Evaluation Report

Tanggal: 2026-03-31
Tujuan: Membandingkan lark vs ANTLR4 untuk memutuskan parser default (ADR-006).

---

## Hasil Tes

Kedua parser diuji pada 5 sample COBOL yang sama, mencakup:
- Fixed-format dan free-format
- COPY/COPYBOOK resolution
- COMP-3, REDEFINES, OCCURS
- IF, EVALUATE TRUE, PERFORM VARYING
- CALL, STRING, nested conditions
- Array access (indexed references)

| Metrik | Lark (Earley) | ANTLR4 |
|---|---|---|
| Parse success | 5/5 | 5/5 |
| Tests passed | 32/32 | 27/27 |
| First-run issues | 2 (format detection, COMP-3 priority) | 0 |
| Parse time (5 samples) | ~3.2s | ~2.7s |

---

## Evaluasi Per Kriteria

### 1. Parse Success / Failure
**Tie.** Kedua parser berhasil parse semua 5 samples setelah bug fix.

Lark butuh 2 fix:
- Terminal priority untuk COMP-3 vs NAME (resolved via `USAGE_TYPE.2`)
- Format detection bug di preprocessor (bukan parser issue)

ANTLR4 langsung pass tanpa fix — lexer rule ordering secara natural menyelesaikan keyword vs identifier priority.

### 2. Effort Implementasi

| Aspek | Lark | ANTLR4 |
|---|---|---|
| Grammar file | ~130 baris | ~180 baris |
| Wrapper code | ~220 baris | ~190 baris |
| External tooling | Tidak ada | Butuh Java + JAR untuk generate code |
| Generated code | Tidak ada | 3 file Python (~3000 baris generated) |
| Debug cycle | Langsung jalankan | Generate → jalankan |

**Lark** lebih mudah untuk iterasi cepat: edit grammar, langsung test.
**ANTLR4** butuh code generation step setiap kali grammar berubah.

### 3. Kualitas Parse Tree

**Lark**: Tree nodes menggunakan rule names sebagai `data`. Token types bisa ambigu tanpa explicit priority annotations. Memerlukan `?` prefix untuk tree flattening.

**ANTLR4**: Strongly-typed context objects per rule. IDE autocomplete bekerja. Tree structure lebih predictable dan lebih mudah di-traverse via visitor pattern.

**ANTLR4 menang** di kualitas tree untuk project jangka panjang.

### 4. Kemudahan Debugging

**Lark**: Error messages cukup informatif. `tree.pretty()` berguna untuk visual inspection. Tapi ambiguity di Earley parser bisa sulit di-trace.

**ANTLR4**: Error messages lebih structured. Banyak tooling tersedia (ANTLRWorks, VS Code extension). Community grammar COBOL85 tersedia sebagai referensi.

**ANTLR4 menang** di debugging dan tooling ecosystem.

### 5. Scalability ke COBOL Dialect Nyata

**Lark**: Grammar harus ditulis sendiri dari nol. Earley parser handle ambiguity tapi lebih lambat. Tidak ada community COBOL grammar.

**ANTLR4**: Community COBOL85 grammar tersedia di `antlr/grammars-v4` repo. Bisa digunakan sebagai basis atau referensi. LALR-based, lebih cepat untuk grammar besar.

**ANTLR4 menang** secara signifikan untuk jangka panjang.

### 6. Deployment / Packaging

**Lark**: Pure Python, zero external dependency selain pip package. Mudah di-bundle.

**ANTLR4**: Runtime Python ringan (`antlr4-python3-runtime`). Tapi butuh Java untuk regenerate parser kalau grammar berubah. Generated files harus di-commit ke repo.

**Lark menang** untuk simplicity deployment.

---

## Rekomendasi

**ANTLR4 sebagai parser default**, dengan alasan:

1. Keyword/identifier priority diselesaikan secara natural oleh lexer rule ordering — tidak perlu workaround priority annotations
2. Community COBOL85 grammar tersedia sebagai upgrade path
3. Strongly-typed visitor pattern lebih maintainable untuk project besar
4. Tooling dan debugging ecosystem lebih mature

**Mitigasi risiko Java dependency:**
- Generated Python files di-commit ke repo
- Contributor hanya butuh Java kalau mengubah grammar
- End user tidak perlu Java sama sekali

**Lark tetap tersedia** sebagai fallback dan untuk quick prototyping.

---

## Keputusan

Lihat ADR-006 di `docs/DECISIONS.md` — status diubah menjadi **Accepted: ANTLR4**.
