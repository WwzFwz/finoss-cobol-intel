# Parser PoC Evaluation Report

Date: 2026-03-31
Objective: Compare lark vs ANTLR4 to decide on the default parser (ADR-006).

---

## Test Results

Both parsers were tested on the same 5 COBOL samples, covering:
- Fixed-format and free-format
- COPY/COPYBOOK resolution
- COMP-3, REDEFINES, OCCURS
- IF, EVALUATE TRUE, PERFORM VARYING
- CALL, STRING, nested conditions
- Array access (indexed references)

| Metric | Lark (Earley) | ANTLR4 |
|---|---|---|
| Parse success | 5/5 | 5/5 |
| Tests passed | 32/32 | 27/27 |
| First-run issues | 2 (format detection, COMP-3 priority) | 0 |
| Parse time (5 samples) | ~3.2s | ~2.7s |

---

## Evaluation Per Criterion

### 1. Parse Success / Failure
**Tie.** Both parsers successfully parsed all 5 samples after bug fixes.

Lark needed 2 fixes:
- Terminal priority for COMP-3 vs NAME (resolved via `USAGE_TYPE.2`)
- Format detection bug in preprocessor (not a parser issue)

ANTLR4 passed immediately without fixes — lexer rule ordering naturally resolves keyword vs identifier priority.

### 2. Implementation Effort

| Aspect | Lark | ANTLR4 |
|---|---|---|
| Grammar file | ~130 lines | ~180 lines |
| Wrapper code | ~220 lines | ~190 lines |
| External tooling | None | Requires Java + JAR for code generation |
| Generated code | None | 3 Python files (~3000 generated lines) |
| Debug cycle | Run directly | Generate → run |

**Lark** is easier for quick iteration: edit grammar, test immediately.
**ANTLR4** requires a code generation step every time the grammar changes.

### 3. Parse Tree Quality

**Lark**: Tree nodes use rule names as `data`. Token types can be ambiguous without explicit priority annotations. Requires `?` prefix for tree flattening.

**ANTLR4**: Strongly-typed context objects per rule. IDE autocomplete works. Tree structure is more predictable and easier to traverse via visitor pattern.

**ANTLR4 wins** on tree quality for long-term projects.

### 4. Ease of Debugging

**Lark**: Error messages are reasonably informative. `tree.pretty()` is useful for visual inspection. But ambiguity in Earley parser can be hard to trace.

**ANTLR4**: Error messages are more structured. Extensive tooling available (ANTLRWorks, VS Code extension). Community COBOL85 grammar available as reference.

**ANTLR4 wins** on debugging and tooling ecosystem.

### 5. Scalability to Real COBOL Dialects

**Lark**: Grammar must be written from scratch. Earley parser handles ambiguity but is slower. No community COBOL grammar available.

**ANTLR4**: Community COBOL85 grammar available in the `antlr/grammars-v4` repo. Can be used as a base or reference. LALR-based, faster for large grammars.

**ANTLR4 wins** significantly for long-term use.

### 6. Deployment / Packaging

**Lark**: Pure Python, zero external dependencies beyond the pip package. Easy to bundle.

**ANTLR4**: Lightweight Python runtime (`antlr4-python3-runtime`). But requires Java to regenerate the parser when the grammar changes. Generated files must be committed to the repo.

**Lark wins** for deployment simplicity.

---

## Recommendation

**ANTLR4 as the default parser**, for the following reasons:

1. Keyword/identifier priority is naturally resolved by lexer rule ordering — no need for priority annotation workarounds
2. Community COBOL85 grammar available as an upgrade path
3. Strongly-typed visitor pattern is more maintainable for large projects
4. Tooling and debugging ecosystem is more mature

**Java dependency mitigation:**
- Generated Python files are committed to the repo
- Contributors only need Java when modifying the grammar
- End users do not need Java at all

**Lark remains available** as a fallback and for quick prototyping.

---

## Decision

See ADR-006 in `docs/DECISIONS.md` — status changed to **Accepted: ANTLR4**.
