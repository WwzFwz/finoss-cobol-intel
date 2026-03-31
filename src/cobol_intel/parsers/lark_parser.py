"""Lark-based COBOL parser implementation."""

from __future__ import annotations

from pathlib import Path

from lark import Lark, Tree, exceptions as lark_exceptions

from cobol_intel.parsers.base import (
    COBOLParser,
    DataItemNode,
    ParagraphNode,
    ParseResult,
    StatementNode,
)

GRAMMAR_PATH = Path(__file__).parent / "cobol.lark"


class LarkCOBOLParser(COBOLParser):
    """COBOL parser using lark with Earley algorithm."""

    def __init__(self) -> None:
        self._parser = Lark(
            GRAMMAR_PATH.read_text(encoding="utf-8"),
            parser="earley",
            ambiguity="resolve",
        )

    @property
    def name(self) -> str:
        return "lark-earley"

    def parse(self, source: str, file_path: str = "") -> ParseResult:
        """Parse preprocessed COBOL source text."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            tree = self._parser.parse(source)
        except lark_exceptions.LarkError as e:
            return ParseResult(
                success=False,
                file_path=file_path,
                errors=[str(e)],
                parser_name=self.name,
            )

        # Extract structured data from the parse tree
        program_id = self._extract_program_id(tree)
        data_items = self._extract_data_items(tree)
        paragraphs = self._extract_paragraphs(tree)
        copybooks = self._extract_copybooks(tree)

        return ParseResult(
            success=True,
            file_path=file_path,
            program_id=program_id,
            tree=tree,
            data_items=data_items,
            paragraphs=paragraphs,
            copybooks_used=copybooks,
            errors=errors,
            warnings=warnings,
            parser_name=self.name,
        )

    def _extract_program_id(self, tree: Tree) -> str | None:
        """Extract PROGRAM-ID from the parse tree."""
        for node in tree.iter_subtrees():
            if node.data == "identification_division":
                # Children: "IDENTIFICATION", "DIVISION", DOT, "PROGRAM-ID", DOT, NAME, DOT
                for child in node.children:
                    if hasattr(child, "type") and child.type == "NAME":
                        return str(child)
        return None

    def _extract_data_items(self, tree: Tree) -> list[DataItemNode]:
        """Extract data items as a flat list, then build hierarchy from level numbers."""
        flat_items: list[DataItemNode] = []

        for node in tree.iter_subtrees():
            if node.data == "data_item":
                item = self._parse_data_item_node(node)
                if item:
                    flat_items.append(item)
            elif node.data == "condition_entry":
                item = self._parse_condition_entry(node)
                if item:
                    flat_items.append(item)

        return self._build_data_hierarchy(flat_items)

    def _parse_data_item_node(self, node: Tree) -> DataItemNode | None:
        """Convert a data_item parse tree node to DataItemNode."""
        level = None
        name = None
        pic = None
        usage = None
        value = None
        redefines = None
        occurs = None

        for child in node.children:
            if hasattr(child, "type"):
                if child.type == "NUMBER" and level is None:
                    level = int(str(child))
                elif child.type == "NAME" and name is None:
                    name = str(child)
                elif child.type == "DOT":
                    continue
            elif isinstance(child, Tree):
                if child.data == "pic_clause":
                    pic = self._get_string_value(child)
                elif child.data == "usage_clause":
                    # USAGE_TYPE is a Token child of usage_clause
                    for uc in child.children:
                        usage = str(uc)
                        break
                elif child.data == "value_clause":
                    value = self._extract_literal_value(child)
                elif child.data == "redefines_clause":
                    redefines = self._get_name(child)
                elif child.data == "occurs_clause":
                    occurs = self._get_number(child)

        if level is not None and name is not None:
            return DataItemNode(
                level=level, name=name, pic=pic, usage=usage,
                value=value, redefines=redefines, occurs=occurs,
            )
        return None

    def _parse_condition_entry(self, node: Tree) -> DataItemNode | None:
        """Convert a condition_entry (88 level) to DataItemNode."""
        name = None
        values: list[str] = []

        for child in node.children:
            if hasattr(child, "type") and child.type == "NAME":
                name = str(child)
            elif isinstance(child, Tree):
                val = self._extract_literal_value(child)
                if val is not None:
                    values.append(val)

        if name:
            return DataItemNode(
                level=88, name=name, is_condition=True,
                condition_values=values,
            )
        return None

    def _extract_paragraphs(self, tree: Tree) -> list[ParagraphNode]:
        """Extract paragraphs from PROCEDURE DIVISION."""
        paragraphs: list[ParagraphNode] = []

        for node in tree.iter_subtrees():
            if node.data == "paragraph":
                name = None
                statements: list[StatementNode] = []

                for child in node.children:
                    if hasattr(child, "type") and child.type == "NAME":
                        name = str(child)
                    elif isinstance(child, Tree) and child.data == "sentence":
                        stmts = self._extract_statements(child)
                        statements.extend(stmts)

                if name:
                    paragraphs.append(ParagraphNode(name=name, statements=statements))

        return paragraphs

    def _extract_statements(self, sentence_node: Tree) -> list[StatementNode]:
        """Extract statements from a sentence."""
        statements: list[StatementNode] = []

        for child in sentence_node.children:
            if isinstance(child, Tree) and child.data != "sentence":
                stmt_type = self._classify_statement(child.data)
                if stmt_type:
                    stmt = StatementNode(type=stmt_type)
                    stmt.target = self._extract_stmt_target(child, stmt_type)
                    stmt.condition = self._extract_stmt_condition(child, stmt_type)
                    # Recursively find nested statements
                    stmt.children = self._find_nested_statements(child)
                    statements.append(stmt)

        return statements

    def _find_nested_statements(self, node: Tree) -> list[StatementNode]:
        """Find statements nested inside compound statements (IF, EVALUATE, etc.)."""
        nested: list[StatementNode] = []
        for child in node.children:
            if isinstance(child, Tree):
                stmt_type = self._classify_statement(child.data)
                if stmt_type:
                    stmt = StatementNode(type=stmt_type)
                    stmt.children = self._find_nested_statements(child)
                    nested.append(stmt)
                elif child.data in ("else_clause", "when_clause", "when_other",
                                     "when_value", "then_block"):
                    # Recurse into blocks
                    nested.extend(self._find_nested_statements(child))
        return nested

    def _classify_statement(self, data: str) -> str | None:
        """Map parse tree node names to statement types."""
        mapping = {
            "display_stmt": "DISPLAY",
            "move_stmt": "MOVE",
            "compute_stmt": "COMPUTE",
            "add_stmt": "ADD",
            "subtract_stmt": "SUBTRACT",
            "multiply_stmt": "MULTIPLY",
            "perform_simple_stmt": "PERFORM",
            "perform_inline_stmt": "PERFORM-VARYING",
            "call_stmt": "CALL",
            "if_stmt": "IF",
            "evaluate_stmt": "EVALUATE",
            "string_stmt": "STRING",
            "stop_stmt": "STOP-RUN",
            "goback_stmt": "GOBACK",
        }
        return mapping.get(data)

    def _extract_stmt_target(self, node: Tree, stmt_type: str) -> str | None:
        """Extract target for CALL and PERFORM statements."""
        if stmt_type == "CALL":
            for child in node.children:
                if hasattr(child, "type") and child.type == "STRING_LIT":
                    return str(child).strip('"').strip("'")
        elif stmt_type == "PERFORM":
            for child in node.children:
                if hasattr(child, "type") and child.type == "NAME":
                    return str(child)
        return None

    def _extract_stmt_condition(self, node: Tree, stmt_type: str) -> str | None:
        """Extract condition text from IF and EVALUATE statements."""
        if stmt_type == "IF":
            for child in node.children:
                if isinstance(child, Tree) and child.data == "condition":
                    return self._tree_to_text(child)
        elif stmt_type == "EVALUATE":
            for child in node.children:
                if isinstance(child, Tree) and child.data == "eval_subject":
                    return self._tree_to_text(child)
        return None

    def _tree_to_text(self, node: Tree) -> str:
        """Flatten a tree node to its text representation."""
        parts: list[str] = []
        for child in node.children:
            if isinstance(child, Tree):
                parts.append(self._tree_to_text(child))
            else:
                parts.append(str(child))
        return " ".join(parts)

    def _extract_copybooks(self, tree: Tree) -> list[str]:
        """Extract COPY statement names."""
        copybooks: list[str] = []
        for node in tree.iter_subtrees():
            if node.data == "copy_entry":
                for child in node.children:
                    if hasattr(child, "type") and child.type == "NAME":
                        copybooks.append(str(child))
        return copybooks

    # --- helpers ---

    def _get_string_value(self, node: Tree) -> str | None:
        """Get string literal value (strip quotes)."""
        for child in node.children:
            if hasattr(child, "type") and child.type == "STRING_LIT":
                return str(child).strip('"').strip("'")
        return None

    def _get_name(self, node: Tree) -> str | None:
        for child in node.children:
            if hasattr(child, "type") and child.type == "NAME":
                return str(child)
        return None

    def _get_number(self, node: Tree) -> int | None:
        for child in node.children:
            if hasattr(child, "type") and child.type == "NUMBER":
                return int(str(child))
        return None

    def _extract_literal_value(self, node: Tree) -> str | None:
        """Extract the value from a literal or value_clause node."""
        for child in node.children:
            if hasattr(child, "type"):
                if child.type in ("STRING_LIT", "NUMBER", "DECIMAL"):
                    return str(child).strip('"').strip("'")
            elif isinstance(child, Tree):
                if child.data in ("string_literal", "number_literal",
                                   "decimal_literal", "fig_const"):
                    return str(child.children[0]) if child.children else None
                # Recurse for nested literal nodes
                val = self._extract_literal_value(child)
                if val is not None:
                    return val
        return None

    def _build_data_hierarchy(self, flat: list[DataItemNode]) -> list[DataItemNode]:
        """Build data item tree from flat list using level numbers."""
        if not flat:
            return []

        roots: list[DataItemNode] = []
        stack: list[DataItemNode] = []

        for item in flat:
            # 88-level items attach to the most recent non-88 item
            if item.level == 88:
                if stack:
                    stack[-1].children.append(item)
                continue

            # Pop items from stack until we find a parent (lower level number)
            while stack and stack[-1].level >= item.level:
                stack.pop()

            if stack:
                stack[-1].children.append(item)
            else:
                roots.append(item)

            stack.append(item)

        return roots
