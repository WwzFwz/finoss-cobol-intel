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


    # Visit a parse tree produced by COBOLParser#replacingClause.
    def visitReplacingClause(self, ctx:COBOLParser.ReplacingClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#replacePair.
    def visitReplacePair(self, ctx:COBOLParser.ReplacePairContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#copyReplaceToken.
    def visitCopyReplaceToken(self, ctx:COBOLParser.CopyReplaceTokenContext):
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


    # Visit a parse tree produced by COBOLParser#procedureUsing.
    def visitProcedureUsing(self, ctx:COBOLParser.ProcedureUsingContext):
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


    # Visit a parse tree produced by COBOLParser#performRangeStmt.
    def visitPerformRangeStmt(self, ctx:COBOLParser.PerformRangeStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#performSimpleStmt.
    def visitPerformSimpleStmt(self, ctx:COBOLParser.PerformSimpleStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#callStmt.
    def visitCallStmt(self, ctx:COBOLParser.CallStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#openStmt.
    def visitOpenStmt(self, ctx:COBOLParser.OpenStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#openPhrase.
    def visitOpenPhrase(self, ctx:COBOLParser.OpenPhraseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#openMode.
    def visitOpenMode(self, ctx:COBOLParser.OpenModeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#closeStmt.
    def visitCloseStmt(self, ctx:COBOLParser.CloseStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#readStmt.
    def visitReadStmt(self, ctx:COBOLParser.ReadStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#atEndClause.
    def visitAtEndClause(self, ctx:COBOLParser.AtEndClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#writeStmt.
    def visitWriteStmt(self, ctx:COBOLParser.WriteStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#rewriteStmt.
    def visitRewriteStmt(self, ctx:COBOLParser.RewriteStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#execSqlStmt.
    def visitExecSqlStmt(self, ctx:COBOLParser.ExecSqlStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#execCicsStmt.
    def visitExecCicsStmt(self, ctx:COBOLParser.ExecCicsStmtContext):
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


    # Visit a parse tree produced by COBOLParser#unstringStmt.
    def visitUnstringStmt(self, ctx:COBOLParser.UnstringStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#inspectStmt.
    def visitInspectStmt(self, ctx:COBOLParser.InspectStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#inspectClause.
    def visitInspectClause(self, ctx:COBOLParser.InspectClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#inspectTallyingClause.
    def visitInspectTallyingClause(self, ctx:COBOLParser.InspectTallyingClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#inspectReplacingClause.
    def visitInspectReplacingClause(self, ctx:COBOLParser.InspectReplacingClauseContext):
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


    # Visit a parse tree produced by COBOLParser#sqlAtom.
    def visitSqlAtom(self, ctx:COBOLParser.SqlAtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by COBOLParser#cicsAtom.
    def visitCicsAtom(self, ctx:COBOLParser.CicsAtomContext):
        return self.visitChildren(ctx)



del COBOLParser