"""
analysis: Graph builder, business rules extractor, and change impact analyzer.

Rules:
- No LLM calls.
- No output formatting.
- Consumes AST from parsers, produces analysis artifacts defined in contracts.
"""

from cobol_intel.analysis.call_graph import build_call_graph
from cobol_intel.analysis.cfg_builder import build_cfg
from cobol_intel.analysis.data_flow import analyze_data_flow
from cobol_intel.analysis.dead_code import detect_dead_code
from cobol_intel.analysis.reference_indexer import build_reference_index
from cobol_intel.analysis.rules_extractor import extract_rules

__all__ = [
    "build_call_graph",
    "build_cfg",
    "analyze_data_flow",
    "detect_dead_code",
    "build_reference_index",
    "extract_rules",
]
