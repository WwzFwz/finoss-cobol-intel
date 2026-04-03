# Contributing to cobol-intel

## Development Setup

```bash
# Clone the repo
git clone https://github.com/WwzFwz/cobol-intel.git
cd cobol-intel

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .\.venv\Scripts\activate  # Windows PowerShell

# Install with dev + api dependencies
pip install -e ".[api,dev]"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cobol_intel

# Run specific test categories
pytest tests/unit/
pytest tests/contract/
pytest tests/integration/
pytest tests/evaluation/
```

## Linting

```bash
ruff check src/ tests/ tools/
```

## Module Boundaries

This project enforces strict module dependency boundaries using [tach](https://docs.gauge.sh/):

```bash
tach check
```

The dependency graph:

```text
contracts (0 deps) <- core <- service <- cli
parsers <- analysis <- service        <- api
llm <- service
outputs <- service
```

Key rules:
- `contracts` and `core` must never import from `cli` or `api`
- `analysis` and `parsers` must not depend on LLM backends
- `cli` and `api` only call `service`, never access internals directly

## Security Reports

Please do not use public issues for security-sensitive reports. Follow
[SECURITY.md](SECURITY.md).

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure `pytest`, `ruff check`, and `tach check` all pass
4. Keep commits focused and well-described
5. Open a PR against `main` with a clear description

## Code Style

- Python 3.11+
- Max line length: 100 characters
- Use type annotations for function signatures
- Follow existing patterns in the module you're modifying
