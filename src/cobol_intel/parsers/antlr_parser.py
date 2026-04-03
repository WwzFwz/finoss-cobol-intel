"""ANTLR4-based COBOL parser implementation."""

from __future__ import annotations

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from cobol_intel.parsers.antlr_gen.COBOLLexer import COBOLLexer
from cobol_intel.parsers.antlr_gen.COBOLParser import COBOLParser as ANTLR4COBOLParser
from cobol_intel.parsers.antlr_gen.COBOLVisitor import COBOLVisitor
from cobol_intel.parsers.base import (
    COBOLParser,
    DataItemNode,
    ParagraphNode,
    ParseResult,
    StatementNode,
)


class _CollectingErrorListener(ErrorListener):
    """Collects parse errors instead of printing to stderr."""

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []

    def syntaxError(self, recognizer, offending, line, column, msg, e):
        self.errors.append(f"line {line}:{column} {msg}")


class _ASTExtractor(COBOLVisitor):
    """Visits the ANTLR4 parse tree and extracts structured data."""

    def __init__(self) -> None:
        self.program_id: str | None = None
        self.procedure_using: list[str] = []
        self.data_items: list[DataItemNode] = []
        self.paragraphs: list[ParagraphNode] = []
        self.copybooks: list[str] = []

    def visitIdentificationDivision(self, ctx):
        # NAME is the program id token
        name_token = ctx.NAME()
        if name_token:
            self.program_id = name_token.getText()
        return self.visitChildren(ctx)

    def visitCopyEntry(self, ctx):
        name_token = ctx.NAME()
        if name_token:
            self.copybooks.append(name_token.getText())
        return self.visitChildren(ctx)

    def visitConditionEntry(self, ctx):
        name_token = ctx.NAME()
        if name_token:
            value = self._extract_literal(ctx.literal())
            self.data_items.append(DataItemNode(
                level=88,
                name=name_token.getText(),
                is_condition=True,
                condition_values=[value] if value else [],
            ))
        return self.visitChildren(ctx)

    def visitProcedureUsing(self, ctx):
        self.procedure_using = [
            name_ref.getText() for name_ref in self._ctx_list(ctx.nameRef())
        ]
        return self.visitChildren(ctx)

    def visitDataItem(self, ctx):
        level = int(ctx.NUMBER().getText())
        name = ctx.NAME().getText()
        pic = None
        usage = None
        value = None
        redefines = None
        occurs = None

        for clause in ctx.dataClause():
            pic_ctx = clause.picClause()
            if pic_ctx:
                raw = pic_ctx.STRING_LIT().getText()
                pic = raw.strip('"').strip("'")

            usage_ctx = clause.usageClause()
            if usage_ctx:
                usage = usage_ctx.getText()

            value_ctx = clause.valueClause()
            if value_ctx:
                value = self._extract_literal(value_ctx.literal())

            occurs_ctx = clause.occursClause()
            if occurs_ctx:
                occurs = int(occurs_ctx.NUMBER().getText())

            redef_ctx = clause.redefinesClause()
            if redef_ctx:
                redefines = redef_ctx.NAME().getText()

        self.data_items.append(DataItemNode(
            level=level, name=name, pic=pic, usage=usage,
            value=value, redefines=redefines, occurs=occurs,
        ))
        # Don't visitChildren — we already extracted everything
        return None

    def visitParagraph(self, ctx):
        name_token = ctx.NAME()
        if name_token:
            para = ParagraphNode(name=name_token.getText())
            for sentence_ctx in ctx.sentence():
                for stmt_ctx in sentence_ctx.statement():
                    stmt = self._extract_statement(stmt_ctx)
                    if stmt:
                        para.statements.append(stmt)
            self.paragraphs.append(para)
        return None  # Don't recurse further

    def _extract_statement(self, ctx) -> StatementNode | None:
        """Map statement context to StatementNode."""
        mapping = [
            ("displayStmt", "DISPLAY"),
            ("moveStmt", "MOVE"),
            ("computeStmt", "COMPUTE"),
            ("addStmt", "ADD"),
            ("subtractStmt", "SUBTRACT"),
            ("multiplyStmt", "MULTIPLY"),
            ("performSimpleStmt", "PERFORM"),
            ("performInlineStmt", "PERFORM-VARYING"),
            ("performRangeStmt", "PERFORM-THRU"),
            ("callStmt", "CALL"),
            ("openStmt", "OPEN"),
            ("closeStmt", "CLOSE"),
            ("readStmt", "READ"),
            ("writeStmt", "WRITE"),
            ("rewriteStmt", "REWRITE"),
            ("execSqlStmt", "EXEC-SQL"),
            ("execCicsStmt", "EXEC-CICS"),
            ("ifStmt", "IF"),
            ("evaluateStmt", "EVALUATE"),
            ("stringStmt", "STRING"),
            ("unstringStmt", "UNSTRING"),
            ("inspectStmt", "INSPECT"),
            ("stopStmt", "STOP-RUN"),
            ("gobackStmt", "GOBACK"),
        ]

        for attr, stmt_type in mapping:
            child = getattr(ctx, attr, lambda: None)()
            if child is not None:
                stmt = StatementNode(type=stmt_type)
                if stmt_type in {"EXEC-SQL", "EXEC-CICS"}:
                    stmt.raw = child.getText()
                stmt.target = self._extract_target(child, stmt_type)
                stmt.condition = self._extract_condition(child, stmt_type)
                stmt.children = self._find_nested_statements(child)
                return stmt
        return None

    def _extract_target(self, ctx, stmt_type: str) -> str | None:
        """Extract target for CALL and PERFORM statements."""
        if stmt_type == "CALL":
            lit = ctx.STRING_LIT()
            if lit:
                return lit.getText().strip('"').strip("'")
        elif stmt_type == "PERFORM":
            name = ctx.NAME()
            if name:
                return name.getText()
        elif stmt_type == "PERFORM-THRU":
            names = self._ctx_list(ctx.NAME())
            if len(names) >= 2:
                return f"{names[0].getText()} THRU {names[1].getText()}"
        elif stmt_type in {"READ", "WRITE", "REWRITE", "CLOSE", "INSPECT"}:
            names = self._ctx_list(ctx.nameRef())
            if names:
                return names[0].getText()
        elif stmt_type == "UNSTRING":
            names = self._ctx_list(ctx.nameRef())
            if names:
                return names[0].getText()
        return None

    def _extract_condition(self, ctx, stmt_type: str) -> str | None:
        """Extract condition text from IF and EVALUATE statements."""
        if stmt_type == "IF":
            cond_ctx = getattr(ctx, "condition", lambda: None)()
            if cond_ctx:
                return cond_ctx.getText()
        elif stmt_type == "EVALUATE":
            subj_ctx = getattr(ctx, "evalSubject", lambda: None)()
            if subj_ctx:
                return subj_ctx.getText()
        return None

    def _find_nested_statements(self, ctx) -> list[StatementNode]:
        """Find nested statements inside compound statements."""
        nested: list[StatementNode] = []

        # Check for statement children directly
        if hasattr(ctx, "statement"):
            for stmt_ctx in ctx.statement():
                stmt = self._extract_statement(stmt_ctx)
                if stmt:
                    nested.append(stmt)

        # Check for elseClause, whenClause
        if hasattr(ctx, "elseClause"):
            else_ctx = ctx.elseClause()
            if else_ctx:
                for stmt_ctx in else_ctx.statement():
                    stmt = self._extract_statement(stmt_ctx)
                    if stmt:
                        nested.append(stmt)

        if hasattr(ctx, "whenClause"):
            for when_ctx in ctx.whenClause():
                for stmt_ctx in when_ctx.statement():
                    stmt = self._extract_statement(stmt_ctx)
                    if stmt:
                        nested.append(stmt)

        if hasattr(ctx, "atEndClause"):
            at_end_ctx = ctx.atEndClause()
            if at_end_ctx:
                for stmt_ctx in at_end_ctx.statement():
                    stmt = self._extract_statement(stmt_ctx)
                    if stmt:
                        nested.append(stmt)

        return nested

    def _extract_literal(self, ctx) -> str | None:
        if ctx is None:
            return None
        if ctx.STRING_LIT():
            return ctx.STRING_LIT().getText().strip('"').strip("'")
        if ctx.DECIMAL():
            return ctx.DECIMAL().getText()
        if ctx.NUMBER():
            return ctx.NUMBER().getText()
        if ctx.figConst():
            return ctx.figConst().getText()
        return None

    def _ctx_list(self, value):
        """Normalize ANTLR context accessors that may return one item or a list."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


class ANTLR4Parser(COBOLParser):
    """COBOL parser using ANTLR4."""

    @property
    def name(self) -> str:
        return "antlr4"

    def parse(self, source: str, file_path: str = "") -> ParseResult:
        """Parse preprocessed COBOL source text."""
        error_listener = _CollectingErrorListener()

        input_stream = InputStream(source)
        lexer = COBOLLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)

        token_stream = CommonTokenStream(lexer)
        parser = ANTLR4COBOLParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)

        tree = parser.program()

        if error_listener.errors:
            return ParseResult(
                success=False,
                file_path=file_path,
                errors=error_listener.errors,
                parser_name=self.name,
            )

        extractor = _ASTExtractor()
        extractor.visit(tree)

        data_items = self._build_data_hierarchy(extractor.data_items)

        return ParseResult(
            success=True,
            file_path=file_path,
            program_id=extractor.program_id,
            procedure_using=extractor.procedure_using,
            tree=tree,
            data_items=data_items,
            paragraphs=extractor.paragraphs,
            copybooks_used=extractor.copybooks,
            parser_name=self.name,
        )

    def _build_data_hierarchy(self, flat: list[DataItemNode]) -> list[DataItemNode]:
        """Build data item tree from flat list using level numbers."""
        if not flat:
            return []

        roots: list[DataItemNode] = []
        stack: list[DataItemNode] = []

        for item in flat:
            if item.level == 88:
                if stack:
                    stack[-1].children.append(item)
                continue

            while stack and stack[-1].level >= item.level:
                stack.pop()

            if stack:
                stack[-1].children.append(item)
            else:
                roots.append(item)

            stack.append(item)

        return roots
