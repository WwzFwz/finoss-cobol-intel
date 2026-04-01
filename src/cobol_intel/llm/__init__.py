"""
llm: Pluggable LLM backend adapters and explanation engine.

Backends: Claude, OpenAI, Ollama, Local.

Rules:
- No parsing logic.
- No direct file I/O.
- All backends implement LLMBackend.
"""

from cobol_intel.llm.backend import LLMBackend, LLMResponse
from cobol_intel.llm.claude_backend import ClaudeBackend
from cobol_intel.llm.explainer import explain_program
from cobol_intel.llm.local_backend import LocalBackend
from cobol_intel.llm.ollama_backend import OllamaBackend
from cobol_intel.llm.openai_backend import OpenAIBackend

__all__ = [
    "LLMBackend",
    "LLMResponse",
    "ClaudeBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "LocalBackend",
    "explain_program",
]
