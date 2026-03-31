# Changelog

All notable changes to cobol-intel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Read-only REST API with versioned endpoints (`/api/v1/`)
- Structured error codes (`ErrorCode` enum) for operational monitoring
- Cross-platform CI pipeline (Linux + Windows, Python 3.11 + 3.12)
- Benchmark suite for parse success rate, latency, and token savings
- Per-program documentation generator (Markdown + HTML)
- Change impact analyzer with call graph traversal and field reference scanning
- Parallel LLM processing with bounded backend-specific concurrency
- File-based explanation cache with composite invalidation keys
- Docker image and docker-compose with optional Ollama sidecar
- `CHANGELOG.md`, `CONTRIBUTING.md`, and GitHub issue templates

## [0.1.0] - 2026-03-31

### Added

- ANTLR4-based COBOL parser with fixed-format and free-format support
- COPYBOOK resolver with circular dependency detection
- Call graph builder and business rules extractor
- Multi-backend LLM explanation engine (Claude, OpenAI, Ollama)
- Context builder with smart chunking and token budget awareness
- Governance layer: audit logging, sensitivity classification, prompt redaction
- Strict policy enforcement and configurable model registry
- Backend retry/timeout and token budget controls
- CLI commands: `analyze`, `explain`, `graph`
- Versioned JSON artifact contracts with Pydantic v2
