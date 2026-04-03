# Generated from COBOL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .COBOLParser import COBOLParser
else:
    from COBOLParser import COBOLParser

# This class defines a complete listener for a parse tree produced by COBOLParser.
class COBOLListener(ParseTreeListener):

    # Enter a parse tree produced by COBOLParser#program.
    def enterProgram(self, ctx:COBOLParser.ProgramContext):
        pass

    # Exit a parse tree produced by COBOLParser#program.
    def exitProgram(self, ctx:COBOLParser.ProgramContext):
        pass


    # Enter a parse tree produced by COBOLParser#identificationDivision.
    def enterIdentificationDivision(self, ctx:COBOLParser.IdentificationDivisionContext):
        pass

    # Exit a parse tree produced by COBOLParser#identificationDivision.
    def exitIdentificationDivision(self, ctx:COBOLParser.IdentificationDivisionContext):
        pass


    # Enter a parse tree produced by COBOLParser#environmentDivision.
    def enterEnvironmentDivision(self, ctx:COBOLParser.EnvironmentDivisionContext):
        pass

    # Exit a parse tree produced by COBOLParser#environmentDivision.
    def exitEnvironmentDivision(self, ctx:COBOLParser.EnvironmentDivisionContext):
        pass


    # Enter a parse tree produced by COBOLParser#inputOutputSection.
    def enterInputOutputSection(self, ctx:COBOLParser.InputOutputSectionContext):
        pass

    # Exit a parse tree produced by COBOLParser#inputOutputSection.
    def exitInputOutputSection(self, ctx:COBOLParser.InputOutputSectionContext):
        pass


    # Enter a parse tree produced by COBOLParser#fileControlParagraph.
    def enterFileControlParagraph(self, ctx:COBOLParser.FileControlParagraphContext):
        pass

    # Exit a parse tree produced by COBOLParser#fileControlParagraph.
    def exitFileControlParagraph(self, ctx:COBOLParser.FileControlParagraphContext):
        pass


    # Enter a parse tree produced by COBOLParser#selectEntry.
    def enterSelectEntry(self, ctx:COBOLParser.SelectEntryContext):
        pass

    # Exit a parse tree produced by COBOLParser#selectEntry.
    def exitSelectEntry(self, ctx:COBOLParser.SelectEntryContext):
        pass


    # Enter a parse tree produced by COBOLParser#dataDivision.
    def enterDataDivision(self, ctx:COBOLParser.DataDivisionContext):
        pass

    # Exit a parse tree produced by COBOLParser#dataDivision.
    def exitDataDivision(self, ctx:COBOLParser.DataDivisionContext):
        pass


    # Enter a parse tree produced by COBOLParser#dataSection.
    def enterDataSection(self, ctx:COBOLParser.DataSectionContext):
        pass

    # Exit a parse tree produced by COBOLParser#dataSection.
    def exitDataSection(self, ctx:COBOLParser.DataSectionContext):
        pass


    # Enter a parse tree produced by COBOLParser#fileEntry.
    def enterFileEntry(self, ctx:COBOLParser.FileEntryContext):
        pass

    # Exit a parse tree produced by COBOLParser#fileEntry.
    def exitFileEntry(self, ctx:COBOLParser.FileEntryContext):
        pass


    # Enter a parse tree produced by COBOLParser#fileDescription.
    def enterFileDescription(self, ctx:COBOLParser.FileDescriptionContext):
        pass

    # Exit a parse tree produced by COBOLParser#fileDescription.
    def exitFileDescription(self, ctx:COBOLParser.FileDescriptionContext):
        pass


    # Enter a parse tree produced by COBOLParser#dataEntry.
    def enterDataEntry(self, ctx:COBOLParser.DataEntryContext):
        pass

    # Exit a parse tree produced by COBOLParser#dataEntry.
    def exitDataEntry(self, ctx:COBOLParser.DataEntryContext):
        pass


    # Enter a parse tree produced by COBOLParser#copyEntry.
    def enterCopyEntry(self, ctx:COBOLParser.CopyEntryContext):
        pass

    # Exit a parse tree produced by COBOLParser#copyEntry.
    def exitCopyEntry(self, ctx:COBOLParser.CopyEntryContext):
        pass


    # Enter a parse tree produced by COBOLParser#replacingClause.
    def enterReplacingClause(self, ctx:COBOLParser.ReplacingClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#replacingClause.
    def exitReplacingClause(self, ctx:COBOLParser.ReplacingClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#replacePair.
    def enterReplacePair(self, ctx:COBOLParser.ReplacePairContext):
        pass

    # Exit a parse tree produced by COBOLParser#replacePair.
    def exitReplacePair(self, ctx:COBOLParser.ReplacePairContext):
        pass


    # Enter a parse tree produced by COBOLParser#copyReplaceToken.
    def enterCopyReplaceToken(self, ctx:COBOLParser.CopyReplaceTokenContext):
        pass

    # Exit a parse tree produced by COBOLParser#copyReplaceToken.
    def exitCopyReplaceToken(self, ctx:COBOLParser.CopyReplaceTokenContext):
        pass


    # Enter a parse tree produced by COBOLParser#conditionEntry.
    def enterConditionEntry(self, ctx:COBOLParser.ConditionEntryContext):
        pass

    # Exit a parse tree produced by COBOLParser#conditionEntry.
    def exitConditionEntry(self, ctx:COBOLParser.ConditionEntryContext):
        pass


    # Enter a parse tree produced by COBOLParser#dataItem.
    def enterDataItem(self, ctx:COBOLParser.DataItemContext):
        pass

    # Exit a parse tree produced by COBOLParser#dataItem.
    def exitDataItem(self, ctx:COBOLParser.DataItemContext):
        pass


    # Enter a parse tree produced by COBOLParser#dataClause.
    def enterDataClause(self, ctx:COBOLParser.DataClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#dataClause.
    def exitDataClause(self, ctx:COBOLParser.DataClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#picClause.
    def enterPicClause(self, ctx:COBOLParser.PicClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#picClause.
    def exitPicClause(self, ctx:COBOLParser.PicClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#usageClause.
    def enterUsageClause(self, ctx:COBOLParser.UsageClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#usageClause.
    def exitUsageClause(self, ctx:COBOLParser.UsageClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#valueClause.
    def enterValueClause(self, ctx:COBOLParser.ValueClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#valueClause.
    def exitValueClause(self, ctx:COBOLParser.ValueClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#occursClause.
    def enterOccursClause(self, ctx:COBOLParser.OccursClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#occursClause.
    def exitOccursClause(self, ctx:COBOLParser.OccursClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#redefinesClause.
    def enterRedefinesClause(self, ctx:COBOLParser.RedefinesClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#redefinesClause.
    def exitRedefinesClause(self, ctx:COBOLParser.RedefinesClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#procedureDivision.
    def enterProcedureDivision(self, ctx:COBOLParser.ProcedureDivisionContext):
        pass

    # Exit a parse tree produced by COBOLParser#procedureDivision.
    def exitProcedureDivision(self, ctx:COBOLParser.ProcedureDivisionContext):
        pass


    # Enter a parse tree produced by COBOLParser#procedureUsing.
    def enterProcedureUsing(self, ctx:COBOLParser.ProcedureUsingContext):
        pass

    # Exit a parse tree produced by COBOLParser#procedureUsing.
    def exitProcedureUsing(self, ctx:COBOLParser.ProcedureUsingContext):
        pass


    # Enter a parse tree produced by COBOLParser#paragraph.
    def enterParagraph(self, ctx:COBOLParser.ParagraphContext):
        pass

    # Exit a parse tree produced by COBOLParser#paragraph.
    def exitParagraph(self, ctx:COBOLParser.ParagraphContext):
        pass


    # Enter a parse tree produced by COBOLParser#sentence.
    def enterSentence(self, ctx:COBOLParser.SentenceContext):
        pass

    # Exit a parse tree produced by COBOLParser#sentence.
    def exitSentence(self, ctx:COBOLParser.SentenceContext):
        pass


    # Enter a parse tree produced by COBOLParser#statement.
    def enterStatement(self, ctx:COBOLParser.StatementContext):
        pass

    # Exit a parse tree produced by COBOLParser#statement.
    def exitStatement(self, ctx:COBOLParser.StatementContext):
        pass


    # Enter a parse tree produced by COBOLParser#displayStmt.
    def enterDisplayStmt(self, ctx:COBOLParser.DisplayStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#displayStmt.
    def exitDisplayStmt(self, ctx:COBOLParser.DisplayStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#moveStmt.
    def enterMoveStmt(self, ctx:COBOLParser.MoveStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#moveStmt.
    def exitMoveStmt(self, ctx:COBOLParser.MoveStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#computeStmt.
    def enterComputeStmt(self, ctx:COBOLParser.ComputeStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#computeStmt.
    def exitComputeStmt(self, ctx:COBOLParser.ComputeStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#addStmt.
    def enterAddStmt(self, ctx:COBOLParser.AddStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#addStmt.
    def exitAddStmt(self, ctx:COBOLParser.AddStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#subtractStmt.
    def enterSubtractStmt(self, ctx:COBOLParser.SubtractStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#subtractStmt.
    def exitSubtractStmt(self, ctx:COBOLParser.SubtractStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#multiplyStmt.
    def enterMultiplyStmt(self, ctx:COBOLParser.MultiplyStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#multiplyStmt.
    def exitMultiplyStmt(self, ctx:COBOLParser.MultiplyStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#performInlineStmt.
    def enterPerformInlineStmt(self, ctx:COBOLParser.PerformInlineStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#performInlineStmt.
    def exitPerformInlineStmt(self, ctx:COBOLParser.PerformInlineStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#performRangeStmt.
    def enterPerformRangeStmt(self, ctx:COBOLParser.PerformRangeStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#performRangeStmt.
    def exitPerformRangeStmt(self, ctx:COBOLParser.PerformRangeStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#performSimpleStmt.
    def enterPerformSimpleStmt(self, ctx:COBOLParser.PerformSimpleStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#performSimpleStmt.
    def exitPerformSimpleStmt(self, ctx:COBOLParser.PerformSimpleStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#callStmt.
    def enterCallStmt(self, ctx:COBOLParser.CallStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#callStmt.
    def exitCallStmt(self, ctx:COBOLParser.CallStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#openStmt.
    def enterOpenStmt(self, ctx:COBOLParser.OpenStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#openStmt.
    def exitOpenStmt(self, ctx:COBOLParser.OpenStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#openPhrase.
    def enterOpenPhrase(self, ctx:COBOLParser.OpenPhraseContext):
        pass

    # Exit a parse tree produced by COBOLParser#openPhrase.
    def exitOpenPhrase(self, ctx:COBOLParser.OpenPhraseContext):
        pass


    # Enter a parse tree produced by COBOLParser#openMode.
    def enterOpenMode(self, ctx:COBOLParser.OpenModeContext):
        pass

    # Exit a parse tree produced by COBOLParser#openMode.
    def exitOpenMode(self, ctx:COBOLParser.OpenModeContext):
        pass


    # Enter a parse tree produced by COBOLParser#closeStmt.
    def enterCloseStmt(self, ctx:COBOLParser.CloseStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#closeStmt.
    def exitCloseStmt(self, ctx:COBOLParser.CloseStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#readStmt.
    def enterReadStmt(self, ctx:COBOLParser.ReadStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#readStmt.
    def exitReadStmt(self, ctx:COBOLParser.ReadStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#atEndClause.
    def enterAtEndClause(self, ctx:COBOLParser.AtEndClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#atEndClause.
    def exitAtEndClause(self, ctx:COBOLParser.AtEndClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#writeStmt.
    def enterWriteStmt(self, ctx:COBOLParser.WriteStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#writeStmt.
    def exitWriteStmt(self, ctx:COBOLParser.WriteStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#rewriteStmt.
    def enterRewriteStmt(self, ctx:COBOLParser.RewriteStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#rewriteStmt.
    def exitRewriteStmt(self, ctx:COBOLParser.RewriteStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#execSqlStmt.
    def enterExecSqlStmt(self, ctx:COBOLParser.ExecSqlStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#execSqlStmt.
    def exitExecSqlStmt(self, ctx:COBOLParser.ExecSqlStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#execCicsStmt.
    def enterExecCicsStmt(self, ctx:COBOLParser.ExecCicsStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#execCicsStmt.
    def exitExecCicsStmt(self, ctx:COBOLParser.ExecCicsStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#ifStmt.
    def enterIfStmt(self, ctx:COBOLParser.IfStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#ifStmt.
    def exitIfStmt(self, ctx:COBOLParser.IfStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#elseClause.
    def enterElseClause(self, ctx:COBOLParser.ElseClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#elseClause.
    def exitElseClause(self, ctx:COBOLParser.ElseClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#evaluateStmt.
    def enterEvaluateStmt(self, ctx:COBOLParser.EvaluateStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#evaluateStmt.
    def exitEvaluateStmt(self, ctx:COBOLParser.EvaluateStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#evalSubject.
    def enterEvalSubject(self, ctx:COBOLParser.EvalSubjectContext):
        pass

    # Exit a parse tree produced by COBOLParser#evalSubject.
    def exitEvalSubject(self, ctx:COBOLParser.EvalSubjectContext):
        pass


    # Enter a parse tree produced by COBOLParser#whenClause.
    def enterWhenClause(self, ctx:COBOLParser.WhenClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#whenClause.
    def exitWhenClause(self, ctx:COBOLParser.WhenClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#whenMatch.
    def enterWhenMatch(self, ctx:COBOLParser.WhenMatchContext):
        pass

    # Exit a parse tree produced by COBOLParser#whenMatch.
    def exitWhenMatch(self, ctx:COBOLParser.WhenMatchContext):
        pass


    # Enter a parse tree produced by COBOLParser#stringStmt.
    def enterStringStmt(self, ctx:COBOLParser.StringStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#stringStmt.
    def exitStringStmt(self, ctx:COBOLParser.StringStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#unstringStmt.
    def enterUnstringStmt(self, ctx:COBOLParser.UnstringStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#unstringStmt.
    def exitUnstringStmt(self, ctx:COBOLParser.UnstringStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#inspectStmt.
    def enterInspectStmt(self, ctx:COBOLParser.InspectStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#inspectStmt.
    def exitInspectStmt(self, ctx:COBOLParser.InspectStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#inspectClause.
    def enterInspectClause(self, ctx:COBOLParser.InspectClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#inspectClause.
    def exitInspectClause(self, ctx:COBOLParser.InspectClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#inspectTallyingClause.
    def enterInspectTallyingClause(self, ctx:COBOLParser.InspectTallyingClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#inspectTallyingClause.
    def exitInspectTallyingClause(self, ctx:COBOLParser.InspectTallyingClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#inspectReplacingClause.
    def enterInspectReplacingClause(self, ctx:COBOLParser.InspectReplacingClauseContext):
        pass

    # Exit a parse tree produced by COBOLParser#inspectReplacingClause.
    def exitInspectReplacingClause(self, ctx:COBOLParser.InspectReplacingClauseContext):
        pass


    # Enter a parse tree produced by COBOLParser#delimTarget.
    def enterDelimTarget(self, ctx:COBOLParser.DelimTargetContext):
        pass

    # Exit a parse tree produced by COBOLParser#delimTarget.
    def exitDelimTarget(self, ctx:COBOLParser.DelimTargetContext):
        pass


    # Enter a parse tree produced by COBOLParser#stopStmt.
    def enterStopStmt(self, ctx:COBOLParser.StopStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#stopStmt.
    def exitStopStmt(self, ctx:COBOLParser.StopStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#gobackStmt.
    def enterGobackStmt(self, ctx:COBOLParser.GobackStmtContext):
        pass

    # Exit a parse tree produced by COBOLParser#gobackStmt.
    def exitGobackStmt(self, ctx:COBOLParser.GobackStmtContext):
        pass


    # Enter a parse tree produced by COBOLParser#condition.
    def enterCondition(self, ctx:COBOLParser.ConditionContext):
        pass

    # Exit a parse tree produced by COBOLParser#condition.
    def exitCondition(self, ctx:COBOLParser.ConditionContext):
        pass


    # Enter a parse tree produced by COBOLParser#simpleCondition.
    def enterSimpleCondition(self, ctx:COBOLParser.SimpleConditionContext):
        pass

    # Exit a parse tree produced by COBOLParser#simpleCondition.
    def exitSimpleCondition(self, ctx:COBOLParser.SimpleConditionContext):
        pass


    # Enter a parse tree produced by COBOLParser#compOp.
    def enterCompOp(self, ctx:COBOLParser.CompOpContext):
        pass

    # Exit a parse tree produced by COBOLParser#compOp.
    def exitCompOp(self, ctx:COBOLParser.CompOpContext):
        pass


    # Enter a parse tree produced by COBOLParser#expression.
    def enterExpression(self, ctx:COBOLParser.ExpressionContext):
        pass

    # Exit a parse tree produced by COBOLParser#expression.
    def exitExpression(self, ctx:COBOLParser.ExpressionContext):
        pass


    # Enter a parse tree produced by COBOLParser#term.
    def enterTerm(self, ctx:COBOLParser.TermContext):
        pass

    # Exit a parse tree produced by COBOLParser#term.
    def exitTerm(self, ctx:COBOLParser.TermContext):
        pass


    # Enter a parse tree produced by COBOLParser#factor.
    def enterFactor(self, ctx:COBOLParser.FactorContext):
        pass

    # Exit a parse tree produced by COBOLParser#factor.
    def exitFactor(self, ctx:COBOLParser.FactorContext):
        pass


    # Enter a parse tree produced by COBOLParser#operand.
    def enterOperand(self, ctx:COBOLParser.OperandContext):
        pass

    # Exit a parse tree produced by COBOLParser#operand.
    def exitOperand(self, ctx:COBOLParser.OperandContext):
        pass


    # Enter a parse tree produced by COBOLParser#nameRef.
    def enterNameRef(self, ctx:COBOLParser.NameRefContext):
        pass

    # Exit a parse tree produced by COBOLParser#nameRef.
    def exitNameRef(self, ctx:COBOLParser.NameRefContext):
        pass


    # Enter a parse tree produced by COBOLParser#literal.
    def enterLiteral(self, ctx:COBOLParser.LiteralContext):
        pass

    # Exit a parse tree produced by COBOLParser#literal.
    def exitLiteral(self, ctx:COBOLParser.LiteralContext):
        pass


    # Enter a parse tree produced by COBOLParser#figConst.
    def enterFigConst(self, ctx:COBOLParser.FigConstContext):
        pass

    # Exit a parse tree produced by COBOLParser#figConst.
    def exitFigConst(self, ctx:COBOLParser.FigConstContext):
        pass


    # Enter a parse tree produced by COBOLParser#sqlAtom.
    def enterSqlAtom(self, ctx:COBOLParser.SqlAtomContext):
        pass

    # Exit a parse tree produced by COBOLParser#sqlAtom.
    def exitSqlAtom(self, ctx:COBOLParser.SqlAtomContext):
        pass


    # Enter a parse tree produced by COBOLParser#cicsAtom.
    def enterCicsAtom(self, ctx:COBOLParser.CicsAtomContext):
        pass

    # Exit a parse tree produced by COBOLParser#cicsAtom.
    def exitCicsAtom(self, ctx:COBOLParser.CicsAtomContext):
        pass



del COBOLParser