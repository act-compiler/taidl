# Generated from IDLV2Expr.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .IDLV2ExprParser import IDLV2ExprParser
else:
    from IDLV2ExprParser import IDLV2ExprParser

# This class defines a complete listener for a parse tree produced by IDLV2ExprParser.
class IDLV2ExprListener(ParseTreeListener):

    # Enter a parse tree produced by IDLV2ExprParser#expression_text.
    def enterExpression_text(self, ctx:IDLV2ExprParser.Expression_textContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#expression_text.
    def exitExpression_text(self, ctx:IDLV2ExprParser.Expression_textContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#constraint_text.
    def enterConstraint_text(self, ctx:IDLV2ExprParser.Constraint_textContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#constraint_text.
    def exitConstraint_text(self, ctx:IDLV2ExprParser.Constraint_textContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#update_text.
    def enterUpdate_text(self, ctx:IDLV2ExprParser.Update_textContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#update_text.
    def exitUpdate_text(self, ctx:IDLV2ExprParser.Update_textContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#update.
    def enterUpdate(self, ctx:IDLV2ExprParser.UpdateContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#update.
    def exitUpdate(self, ctx:IDLV2ExprParser.UpdateContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#expression.
    def enterExpression(self, ctx:IDLV2ExprParser.ExpressionContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#expression.
    def exitExpression(self, ctx:IDLV2ExprParser.ExpressionContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#additive.
    def enterAdditive(self, ctx:IDLV2ExprParser.AdditiveContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#additive.
    def exitAdditive(self, ctx:IDLV2ExprParser.AdditiveContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#multiplicative.
    def enterMultiplicative(self, ctx:IDLV2ExprParser.MultiplicativeContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#multiplicative.
    def exitMultiplicative(self, ctx:IDLV2ExprParser.MultiplicativeContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#unary.
    def enterUnary(self, ctx:IDLV2ExprParser.UnaryContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#unary.
    def exitUnary(self, ctx:IDLV2ExprParser.UnaryContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#atom.
    def enterAtom(self, ctx:IDLV2ExprParser.AtomContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#atom.
    def exitAtom(self, ctx:IDLV2ExprParser.AtomContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#reference.
    def enterReference(self, ctx:IDLV2ExprParser.ReferenceContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#reference.
    def exitReference(self, ctx:IDLV2ExprParser.ReferenceContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#condition.
    def enterCondition(self, ctx:IDLV2ExprParser.ConditionContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#condition.
    def exitCondition(self, ctx:IDLV2ExprParser.ConditionContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#conjunction.
    def enterConjunction(self, ctx:IDLV2ExprParser.ConjunctionContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#conjunction.
    def exitConjunction(self, ctx:IDLV2ExprParser.ConjunctionContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#comparison.
    def enterComparison(self, ctx:IDLV2ExprParser.ComparisonContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#comparison.
    def exitComparison(self, ctx:IDLV2ExprParser.ComparisonContext):
        pass


    # Enter a parse tree produced by IDLV2ExprParser#compare.
    def enterCompare(self, ctx:IDLV2ExprParser.CompareContext):
        pass

    # Exit a parse tree produced by IDLV2ExprParser#compare.
    def exitCompare(self, ctx:IDLV2ExprParser.CompareContext):
        pass



del IDLV2ExprParser