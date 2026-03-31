"""
llm: Pluggable LLM backend adapters.

Backends: Claude, OpenAI, Ollama, local model.

Rules:
- No parsing logic.
- No direct file I/O.
- All backends implement LLMBackend from core.
"""
