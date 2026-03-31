"""
analysis: Graph builder, business rules extractor, and change impact analyzer.

Rules:
- No LLM calls.
- No output formatting.
- Consumes AST from parsers, produces analysis artifacts defined in contracts.
"""

from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.analysis.rules_extractor import extract_rules

__all__ = ["build_call_graph", "extract_rules"]
