# Generated from COBOL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .COBOLParser import COBOLParser
else:
    from COBOLParser import COBOLParser

# This class defines a complete generic visitor for a parse tree produced by COBOLParser.

class COBOLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by COBOLParser#program.
    def visitProgram(self, ctx:COBOLParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#identificationDivision.
    def visitIdentificationDivision(self, ctx:COBOLParser.IdentificationDivisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#environmentDivision.
    def visitEnvironmentDivision(self, ctx:COBOLParser.EnvironmentDivisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#inputOutputSection.
    def visitInputOutputSection(self, ctx:COBOLParser.InputOutputSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#fileControlParagraph.
    def visitFileControlParagraph(self, ctx:COBOLParser.FileControlParagraphContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#selectEntry.
    def visitSelectEntry(self, ctx:COBOLParser.SelectEntryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#dataDivision.
    def visitDataDivision(self, ctx:COBOLParser.DataDivisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#dataSection.
    def visitDataSection(self, ctx:COBOLParser.DataSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#fileEntry.
    def visitFileEntry(self, ctx:COBOLParser.FileEntryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#fileDescription.
    def visitFileDescription(self, ctx:COBOLParser.FileDescriptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#dataEntry.
    def visitDataEntry(self, ctx:COBOLParser.DataEntryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#copyEntry.
    def visitCopyEntry(self, ctx:COBOLParser.CopyEntryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#conditionEntry.
    def visitConditionEntry(self, ctx:COBOLParser.ConditionEntryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#dataItem.
    def visitDataItem(self, ctx:COBOLParser.DataItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#dataClause.
    def visitDataClause(self, ctx:COBOLParser.DataClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#picClause.
    def visitPicClause(self, ctx:COBOLParser.PicClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#usageClause.
    def visitUsageClause(self, ctx:COBOLParser.UsageClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#valueClause.
    def visitValueClause(self, ctx:COBOLParser.ValueClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#occursClause.
    def visitOccursClause(self, ctx:COBOLParser.OccursClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#redefinesClause.
    def visitRedefinesClause(self, ctx:COBOLParser.RedefinesClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#procedureDivision.
    def visitProcedureDivision(self, ctx:COBOLParser.ProcedureDivisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#paragraph.
    def visitParagraph(self, ctx:COBOLParser.ParagraphContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#sentence.
    def visitSentence(self, ctx:COBOLParser.SentenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#statement.
    def visitStatement(self, ctx:COBOLParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#displayStmt.
    def visitDisplayStmt(self, ctx:COBOLParser.DisplayStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#moveStmt.
    def visitMoveStmt(self, ctx:COBOLParser.MoveStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#computeStmt.
    def visitComputeStmt(self, ctx:COBOLParser.ComputeStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#addStmt.
    def visitAddStmt(self, ctx:COBOLParser.AddStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#subtractStmt.
    def visitSubtractStmt(self, ctx:COBOLParser.SubtractStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#multiplyStmt.
    def visitMultiplyStmt(self, ctx:COBOLParser.MultiplyStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#performInlineStmt.
    def visitPerformInlineStmt(self, ctx:COBOLParser.PerformInlineStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#performSimpleStmt.
    def visitPerformSimpleStmt(self, ctx:COBOLParser.PerformSimpleStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#callStmt.
    def visitCallStmt(self, ctx:COBOLParser.CallStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#ifStmt.
    def visitIfStmt(self, ctx:COBOLParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#elseClause.
    def visitElseClause(self, ctx:COBOLParser.ElseClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#evaluateStmt.
    def visitEvaluateStmt(self, ctx:COBOLParser.EvaluateStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#evalSubject.
    def visitEvalSubject(self, ctx:COBOLParser.EvalSubjectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#whenClause.
    def visitWhenClause(self, ctx:COBOLParser.WhenClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#whenMatch.
    def visitWhenMatch(self, ctx:COBOLParser.WhenMatchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#stringStmt.
    def visitStringStmt(self, ctx:COBOLParser.StringStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#delimTarget.
    def visitDelimTarget(self, ctx:COBOLParser.DelimTargetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#stopStmt.
    def visitStopStmt(self, ctx:COBOLParser.StopStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#gobackStmt.
    def visitGobackStmt(self, ctx:COBOLParser.GobackStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#condition.
    def visitCondition(self, ctx:COBOLParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#simpleCondition.
    def visitSimpleCondition(self, ctx:COBOLParser.SimpleConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#compOp.
    def visitCompOp(self, ctx:COBOLParser.CompOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#expression.
    def visitExpression(self, ctx:COBOLParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#term.
    def visitTerm(self, ctx:COBOLParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#factor.
    def visitFactor(self, ctx:COBOLParser.FactorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#operand.
    def visitOperand(self, ctx:COBOLParser.OperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#nameRef.
    def visitNameRef(self, ctx:COBOLParser.NameRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#literal.
    def visitLiteral(self, ctx:COBOLParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#figConst.
    def visitFigConst(self, ctx:COBOLParser.FigConstContext):
        return self.visitChildren(ctx)



del COBOLParser