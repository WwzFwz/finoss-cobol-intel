"""Base parser interface.

All parser implementations (lark, ANTLR4, etc.) must implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cobol_intel.contracts.source_ref import SourceRef


@dataclass
class ParseResult:
    """Result of parsing a COBOL program."""

    success: bool
    file_path: str = ""
    program_id: str | None = None
    tree: Any = None  # Parser-specific tree (lark Tree, ANTLR4 tree, etc.)
    data_items: list[DataItemNode] = field(default_factory=list)
    paragraphs: list[ParagraphNode] = field(default_factory=list)
    copybooks_used: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parser_name: str = ""


@dataclass
class DataItemNode:
    """Parsed data item from DATA DIVISION."""

    level: int
    name: str
    pic: str | None = None
    usage: str | None = None
    value: str | None = None
    redefines: str | None = None
    occurs: int | None = None
    is_condition: bool = False
    condition_values: list[str] = field(default_factory=list)
    children: list[DataItemNode] = field(default_factory=list)
    source: SourceRef | None = None


@dataclass
class ParagraphNode:
    """Parsed paragraph from PROCEDURE DIVISION."""

    name: str
    statements: list[StatementNode] = field(default_factory=list)
    source: SourceRef | None = None


@dataclass
class StatementNode:
    """Parsed statement."""

    type: str  # DISPLAY, MOVE, IF, EVALUATE, PERFORM, CALL, COMPUTE, etc.
    raw: str = ""  # Raw text of the statement (for debugging)
    target: str | None = None  # CALL target program or PERFORM target paragraph
    condition: str | None = None  # Condition text for IF/EVALUATE/WHEN
    children: list[StatementNode] = field(default_factory=list)
    source: SourceRef | None = None


class COBOLParser(ABC):
    """Abstract base class for COBOL parsers."""

    @abstractmethod
    def parse(self, source: str, file_path: str = "") -> ParseResult:
        """Parse preprocessed COBOL source text."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this parser implementation."""
        ...
