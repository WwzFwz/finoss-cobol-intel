# Architecture Deep Dive

This document explains the architectural decisions and the reasoning behind them.
The main focus is to build an MVP that can actually be built, tested, and
integrated, without jumping too quickly into full enterprise complexity.

---

## Architecture Priorities

Architecture priorities for the initial phase:

1. The parser and static analysis must be robust enough for real COBOL samples.
2. Output must have a stable and versioned contract.
3. The core pipeline must be useful even when the LLM is turned off.
4. CLI, API, and GUI should eventually share the same foundation through services and contracts.

---

## Why Static Analysis First, Not Jumping Straight to LLM

LLM without preprocessing on COBOL has fundamental problems:

| Problem | Impact | Solution in this project |
|---|---|---|
| COPYBOOK not resolved | LLM guesses the contents of data structures | Resolver before LLM |
| CALL to other programs unknown | Incomplete analysis | Call graph builder |
| Very large programs | Exceeds context window | Smart chunking with context |
| COMP-3 / packed decimal | Often misinterpreted | Type-aware AST |
| Non-descriptive variables | LLM has difficulty inferring meaning | Enrichment from surrounding context |

Conclusion: **LLM is only used after the data is clean and structured.**

---

## Package Boundaries

The package architecture must keep the dependency flow healthy:

```text
contracts <- core <- service <- cli
parsers   <- analysis <- service
llm       <- service
outputs   <- service
```

Explanation:

- `contracts` contains schemas, manifests, and DTOs that serve as the shared language.
- `core` contains domain abstractions and orchestration interfaces that do not
  depend on the UI.
- `parsers` and `analysis` produce core artifacts that can be used without the LLM.
- `service` combines the pipeline, run lifecycle, and artifact writing.
- `cli` is merely the calling layer.

Implications:

- If an API or GUI is added later, both must go through `service`.
- Do not place parsing logic, graph analysis, or formatting directly in the CLI.

---

## Canonical Output Contracts

This project needs to have stable output before adding an API or GUI.

Minimum artifact contracts that must exist:

- `manifest.json`
- `ast/<program>.json`
- `graphs/dependency_graph.json`
- `rules/business_rules.json`

All JSON artifacts must have:

- `schema_version`
- `tool_version`
- `generated_at`

For `manifest.json` specifically, the minimum fields are:

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

The main purposes of this contract:

- easy for other systems to parse
- can be reused without rerunning the pipeline
- safe for regression testing
- serves as the foundation for a future API and GUI

---

## Run Lifecycle And Artifact Model

Although full database persistence is deferred, all executions must be treated
as explicit `analysis run` instances.

Minimum lifecycle:

```text
queued -> running -> completed
queued -> running -> failed
```

Each run writes artifacts to the filesystem with this structure:

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

Why this matters:

- CLI can display the results of the latest run
- A future API can read the same artifacts
- A future GUI only needs to browse the manifest and artifacts, without direct coupling to parser internals
- This storage can be migrated to object storage or a DB layer later without changing the semantic model

---

## Parser Strategy

The parser is the foundation of the entire system, so parser decisions should not
be made based solely on library preference.

### Candidate A: Lark

Strengths:

- Pure Python
- Easy to integrate into the codebase
- Flexible for custom grammars

Risks:

- COBOL grammar must be largely written manually
- Can be slow or fragile for complex dialects

### Candidate B: ANTLR4 COBOL Grammar

Strengths:

- There is an existing grammar that can serve as a starting point
- More realistic for quick validation against real COBOL

Risks:

- Heavier tooling
- Community grammar still needs to be validated and adapted

### Decision Gate

Phase 0 must run a small PoC on at least 3-4 real COBOL samples:

- simple fixed-format
- simple free-format
- sample with `COPY`
- sample with `COMP-3`, `REDEFINES`, or `CALL`

Initial evaluation metrics:

- parse success / fail
- preprocessing implementation effort
- quality of the parse tree for internal AST needs
- ease of debugging on failure

Only after that is the default parser locked in.

---

## Known Dialect Gaps

Current parser coverage is sufficient for MVP static analysis, but that does not
mean this project already handles all real COBOL dialects found in banks or
enterprise mainframes.

### Already Covered In MVP

- fixed-format and free-format source
- `IDENTIFICATION`, `ENVIRONMENT`, `DATA`, and `PROCEDURE DIVISION`
- `WORKING-STORAGE`, `FILE`, and `LINKAGE SECTION`
- `COPY`, circular `COPY` warning, and `COPY ... REPLACING`
- `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, level-88 conditions
- `PROCEDURE DIVISION USING`
- `IF`, `EVALUATE`, `PERFORM`, `PERFORM THRU`, `CALL`, `STRING`, `UNSTRING`, `INSPECT`,
  `GOBACK`, `STOP RUN`
- file I/O statements: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- `EXEC SQL` subset for static analysis context extraction
- basic `EXEC CICS` block extraction for static analysis context

### Not Yet Fully Covered

- Broader `EXEC SQL`: multi-statement, host variable edge cases,
  vendor-specific SQL embedding, and statements beyond the current subset
- Broader `EXEC CICS`: transaction verbs, HANDLE CONDITION, and
  more complex options beyond basic block extraction
- `GO TO`, `ALTER`, and other legacy control-flow constructs
- `SEARCH`, `SEARCH ALL`, and richer variants of `UNSTRING` / `INSPECT`
- `OCCURS DEPENDING ON`, `INDEXED BY`, `RENAMES`
- vendor-specific syntax from IBM Enterprise COBOL, Micro Focus, and GnuCOBOL

### Most Valuable Dialect Roadmap

For real finance codebases, the most sensible priority order is:

1. `EXEC SQL` expansion
2. `EXEC CICS` expansion
3. `SEARCH` / `SEARCH ALL`
4. broader `UNSTRING` and `INSPECT` variants
5. `GO TO` / legacy control-flow if your target is truly mainframe-heavy

Reasoning behind this priority:

- `EXEC SQL` is very common in core banking and batch processing systems
  connected to DB2 or other databases, so expanding it still has high ROI.
- `EXEC CICS` and `SEARCH` frequently appear in older legacy codebases
  closer to mainframe transaction processing.
- Richer `UNSTRING` / `INSPECT` variants are important for string cleaning and
  parsing in finance batch processing.
- `EXEC CICS` is very important at some large banks, but not all fintech
  or modernization use cases require it in the early phase.

In other words, the best next target is not "all dialects", but rather
"the enterprise-heavy subset that most frequently appears in finance workloads".

---

## Smart Chunking Strategy

For large programs that exceed the LLM context window:

```text
Large COBOL program
    |
    v
Split per section or paragraph boundary
    |
    v
Add an envelope per chunk:
  - relevant global data definitions
  - overall program summary
  - paragraphs that call or are called by this chunk
    |
    v
LLM analyzes each chunk with sufficient context
    |
    v
Merge and deduplicate results
```

Key principles:

- Chunking must not arbitrarily cut statements.
- Chunking must be based on program structure, not merely token count.

---

## Traceability

One of the main selling points of this project is that results can be traced back
to the COBOL source.

Every business rule or explanation should ideally contain:

- source file
- source paragraph or section
- source line range
- originating artifact, such as the related AST node or graph edge

Example rule format:

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
  "description": "Premium rate applies to Savings accounts with a certain balance."
}
```

Without traceability, LLM results will look like a demo. With traceability,
the results are more suitable for documentation, auditing, and human review.

---

## LLM Backend Architecture

The model backend must be pluggable and not alter the core pipeline.

```python
class LLMBackend(ABC):
    @abstractmethod
    def explain(self, context: "COBOLContext", mode: "ExplanationMode") -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize_rules(self, rules: list["BusinessRule"], mode: "ExplanationMode") -> str:
        raise NotImplementedError
```

Target implementations:

- `OpenAIBackend`
- `ClaudeBackend`
- `OllamaBackend`
- `LocalModelBackend`

Notes:

- Static analysis must not depend on this backend.
- If no LLM backend is available, static analysis artifacts must still be produced.

---

## Governance And Safe Integration

For fintech and banks, an explain pipeline is not enough if it just "works".
The pipeline must also answer:

- what model was used?
- how sensitive is the data?
- has the prompt to the cloud been redacted?
- who executed this run?
- how many tokens were consumed?

For this reason, the architecture now adds two lightweight governance layers:

1. `governance` summary in `manifest.json`
2. `logs/audit_events.jsonl` as a per-run event trail

The goal is not to replace a corporate SIEM or audit database, but to provide
a technical source-of-truth from this tool that can later be forwarded to their systems.

### Audit Log Ownership

This tool's audit log records things that typically do not exist in corporate
business audit logs:

- backend and model used
- success/failure of each explain step
- sensitivity classification of artifacts
- redactions applied
- token usage per run

If a company wants to store everything in their DB or logging stack, this source
can be forwarded. However, technical events should still be produced by the tool.

### Sensitivity And Prompt Redaction

Before a prompt is sent to a cloud backend, AST artifacts can be classified as:

- `low`
- `moderate`
- `high`
- `restricted`

For `high` and `restricted` workloads, cloud prompts should go through a redaction
helper. This is not a perfect DLP solution, but it serves as an initial guardrail
so the integration does not "just send everything to the API".

### Model Registry And Presets

An approved model registry is used to prevent backends/models from being chosen
arbitrarily. Initial presets provided:

- `fast`
- `balanced`
- `audit`
- `local-only`

These presets are the foundation for policy routing in the next phase. Their purpose:

- cloud for non-sensitive workloads
- local/on-prem for sensitive workloads
- model approval easier to audit

This registry can now be read from `config/llm_policy.json` or another JSON path
provided at runtime, so each deployment has its own approval policy without
modifying source code.

### Strict Policy And Token Budget

Warnings alone are not enough for regulated environments. Therefore the explain pipeline
can now be run in strict mode:

- if a sensitive artifact is routed to a cloud backend, the request can be blocked
- if the model is not in the approved registry deployment, the request can be blocked
- token usage per explain run can be capped so costs do not spiral out of control

The purpose of this feature is not to replace a full platform governance solution, but to provide
real guardrails when the tool is used in an enterprise pilot or technical review.

---

## On-Premise Deployment

For banks that cannot send code to the cloud, the baseline deployment is:

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

Not yet targeted for MVP:

- multi-tenant isolation
- enterprise auth and RBAC
- central admin dashboard

However, the architecture is intentionally designed so these features can be added later
on top of the stable service layer and contracts.

---

## GUI And API Positioning

### CLI-First

CLI is the first interface because:

- it delivers value to developers the fastest
- easy to integrate into scripts and CI/CD
- easiest to test

### API Later

An API is worth adding after:

- manifest and artifact contracts are stable
- service layer is stable
- regression tests are robust enough

### GUI Later

A GUI is useful for demos, non-technical stakeholders, and artifact browsing, but:

- it must not come before contracts are stable
- it must not depend directly on parser internals
- it should remain in a single repo for now until the backend interface matures

---

## Testing Architecture

Testing must be divided into several layers:

### Parser Corpus Tests

Validate the parser on COBOL samples across sources and dialects.

### Contract Tests

Validate all JSON output against schemas in `contracts/`.

### Regression Tests

Commit expected artifacts for important samples so parser changes are easy to detect.

### LLM Evaluation

Compare raw LLM vs the preprocessing pipeline for accuracy, token usage, and traceability.

---

## Summary

This project's architecture is intentionally optimized for the following order:

1. a validated parser
2. stable output contracts
3. a reusable service layer
4. a pluggable LLM
5. API and GUI as consumers, not the center of logic

With this order, the project remains attractive as an AI portfolio piece, while also
looking like software that is truly ready to be integrated into an enterprise environment.
