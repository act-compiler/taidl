# Generated from IDLV2Expr.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .IDLV2ExprParser import IDLV2ExprParser
else:
    from IDLV2ExprParser import IDLV2ExprParser

# This class defines a complete generic visitor for a parse tree produced by IDLV2ExprParser.

class IDLV2ExprVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by IDLV2ExprParser#expression_text.
    def visitExpression_text(self, ctx:IDLV2ExprParser.Expression_textContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#constraint_text.
    def visitConstraint_text(self, ctx:IDLV2ExprParser.Constraint_textContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#update_text.
    def visitUpdate_text(self, ctx:IDLV2ExprParser.Update_textContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#update.
    def visitUpdate(self, ctx:IDLV2ExprParser.UpdateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#expression.
    def visitExpression(self, ctx:IDLV2ExprParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#additive.
    def visitAdditive(self, ctx:IDLV2ExprParser.AdditiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#multiplicative.
    def visitMultiplicative(self, ctx:IDLV2ExprParser.MultiplicativeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#unary.
    def visitUnary(self, ctx:IDLV2ExprParser.UnaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#atom.
    def visitAtom(self, ctx:IDLV2ExprParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#reference.
    def visitReference(self, ctx:IDLV2ExprParser.ReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#condition.
    def visitCondition(self, ctx:IDLV2ExprParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#conjunction.
    def visitConjunction(self, ctx:IDLV2ExprParser.ConjunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#comparison.
    def visitComparison(self, ctx:IDLV2ExprParser.ComparisonContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IDLV2ExprParser#compare.
    def visitCompare(self, ctx:IDLV2ExprParser.CompareContext):
        return self.visitChildren(ctx)



del IDLV2ExprParser