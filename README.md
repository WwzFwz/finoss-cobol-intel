# cobol-intel

[![CI](https://github.com/WwzFwz/cobol-intel/actions/workflows/ci.yml/badge.svg)](https://github.com/WwzFwz/cobol-intel/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Open-source static analysis and LLM explanation platform for legacy COBOL
codebases. Built for banking, fintech, and regulated modernization workflows.

## Why This Exists

Legacy COBOL systems fail the same way: key maintainers retire, documentation
goes stale, impact analysis is manual, and regulators still need clear
explanations. `cobol-intel` fixes that with a structured pipeline:

```
COBOL source → parser & AST → call graph & business rules → LLM explanation
                                                           → impact analysis
                                                           → documentation
```

The LLM consumes clean, traceable artifacts — not raw COBOL.

## Quickstart

```bash
pip install cobol-intel

# Analyze a COBOL directory
cobol-intel analyze samples/ --copybook-dir copybooks

# Explain with an LLM backend
cobol-intel explain samples/complex/payment.cbl --model claude --mode business

# Generate documentation
cobol-intel docs artifacts/samples/run_xxx --format html

# Analyze change impact
cobol-intel impact artifacts/samples/run_xxx --changed-program PAYMENT --changed-field WS-BALANCE
```

Output:

```
[cobol-intel] analyze: samples/
Run ID: run_20260401_001
Status: completed
Artifacts: artifacts/samples/run_20260401_001
```

## Features

### Static Analysis
- ANTLR4-based parser (fixed + free format COBOL)
- COPYBOOK resolution with circular dependency detection
- Call graph builder and business rules extractor
- Control flow graph (CFG) with branch, perform, and fallthrough edges
- Field-level data flow analysis (MOVE, COMPUTE, READ INTO, WRITE FROM, CALL)
- Dead code detection: unreachable paragraphs, unused data items, dead branches
- Field reference indexer with read/write/condition classification
- Data item hierarchy with PIC, COMP-3, REDEFINES, OCCURS, level-88

### LLM Explanation
- Multi-backend: Claude, OpenAI, Ollama
- Three modes: `technical`, `business`, `audit`
- Governance: audit logging, sensitivity classification, prompt redaction
- Policy enforcement, token budgets, retry/timeout
- Parallel processing with bounded concurrency
- File-based cache with composite keys

### Change Impact Analysis
- "If I change field X, what breaks?"
- BFS traversal on reverse call graph
- Field reference scanning across ASTs and business rules
- Configurable depth limit

### Output & Documentation
- Versioned JSON artifact contracts (Pydantic v2)
- Markdown + HTML report generation
- Self-contained HTML with sidebar nav, search, and Mermaid graphs
- Structured error codes for operational monitoring

### API & Distribution
- Versioned REST API (`/api/v1/`) with OpenAPI docs and typed error responses
- Docker image + docker-compose with optional Ollama sidecar
- Cross-platform CI (Linux + Windows, Python 3.11 + 3.12)

## CLI Commands

| Command | Description |
|---------|-------------|
| `analyze` | Parse COBOL files, build AST, call graph, business rules |
| `explain` | Run analysis + LLM explanation |
| `graph` | Build dependency and call graph artifacts |
| `impact` | Analyze change impact from a completed run |
| `docs` | Generate documentation (Markdown or HTML) |

Global:

```bash
cobol-intel --version           # Show version
```

Key flags:

```bash
--model claude|openai|ollama    # LLM backend
--mode technical|business|audit # Explanation style
--parallel                      # Enable parallel LLM processing
--max-workers N                 # Override concurrency limit
--cache / --no-cache            # Explanation cache toggle
--strict-policy                 # Hard block policy violations
--max-tokens-per-run N          # Token budget cap
--format markdown|html          # Documentation format
```

## API Usage

```bash
pip install cobol-intel[api]
cobol-intel-api  # starts on port 8000

curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/runs?output_dir=artifacts
curl http://localhost:8000/api/v1/version
```

See [docs/API_GUIDE.md](docs/API_GUIDE.md) for full endpoint reference.

## Output Artifacts

Each run produces a stable artifact tree:

```
artifacts/<project>/<run_id>/
  manifest.json          # Run metadata, governance, errors
  ast/                   # Per-program AST JSON
  graphs/                # Call graph JSON + Mermaid
  rules/                 # Business rules JSON + Markdown
  analysis/              # CFG, data flow, dead code, references
  docs/                  # Explanations, documentation
  logs/                  # Audit event log
```

See [docs/OUTPUT_GALLERY.md](docs/OUTPUT_GALLERY.md) for sample artifacts.

## COBOL Subset Coverage

- Fixed-format and free-format COBOL
- `COPY`, circular copy detection, `COPY ... REPLACING`
- `WORKING-STORAGE`, `FILE`, `LINKAGE` sections
- `PROCEDURE DIVISION USING`
- `PIC`, `COMP-3`, `REDEFINES`, `OCCURS`, level-88 conditions
- `IF`, `EVALUATE`, `PERFORM`, `CALL`, `STRING`, `UNSTRING`, `INSPECT`
- File I/O: `OPEN`, `READ`, `WRITE`, `REWRITE`, `CLOSE`
- `EXEC SQL` subset for static-analysis context

## Development

```bash
git clone https://github.com/WwzFwz/cobol-intel.git
cd cobol-intel
pip install -e ".[dev]"

make lint    # ruff + tach
make test    # pytest
make bench   # benchmark suite
make build   # build wheel
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full dev setup and guidelines.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Architecture Decisions](docs/DECISIONS.md)
- [API Guide](docs/API_GUIDE.md)
- [Output Gallery](docs/OUTPUT_GALLERY.md)
- [Fintech Readiness](docs/FINTECH_READINESS.md)
- [Parser Evaluation](docs/PARSER_EVALUATION.md)
- [Project Plan](docs/PLAN.md)
- [Progress](docs/PROGRESS.md)
- [Changelog](CHANGELOG.md)

## License

MIT
