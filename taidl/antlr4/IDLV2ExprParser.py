# Generated from IDLV2Expr.g4 by ANTLR 4.9.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\31")
        buf.write("i\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16\t")
        buf.write("\16\4\17\t\17\3\2\3\2\3\2\3\3\3\3\3\3\3\4\3\4\3\4\3\5")
        buf.write("\3\5\3\5\3\5\3\6\3\6\3\7\3\7\3\7\7\7\61\n\7\f\7\16\7\64")
        buf.write("\13\7\3\b\3\b\3\b\7\b9\n\b\f\b\16\b<\13\b\3\t\3\t\3\t")
        buf.write("\5\tA\n\t\3\n\3\n\3\n\3\n\3\n\3\n\5\nI\n\n\3\13\3\13\3")
        buf.write("\f\3\f\3\f\7\fP\n\f\f\f\16\fS\13\f\3\r\3\r\3\r\7\rX\n")
        buf.write("\r\f\r\16\r[\13\r\3\16\3\16\3\16\3\16\3\16\3\16\3\16\3")
        buf.write("\16\5\16e\n\16\3\17\3\17\3\17\2\2\20\2\4\6\b\n\f\16\20")
        buf.write("\22\24\26\30\32\34\2\6\3\2\17\20\3\2\21\23\3\2\5\7\3\2")
        buf.write("\t\16\2b\2\36\3\2\2\2\4!\3\2\2\2\6$\3\2\2\2\b\'\3\2\2")
        buf.write("\2\n+\3\2\2\2\f-\3\2\2\2\16\65\3\2\2\2\20@\3\2\2\2\22")
        buf.write("H\3\2\2\2\24J\3\2\2\2\26L\3\2\2\2\30T\3\2\2\2\32d\3\2")
        buf.write("\2\2\34f\3\2\2\2\36\37\5\n\6\2\37 \7\2\2\3 \3\3\2\2\2")
        buf.write("!\"\5\26\f\2\"#\7\2\2\3#\5\3\2\2\2$%\5\b\5\2%&\7\2\2\3")
        buf.write("&\7\3\2\2\2\'(\7\7\2\2()\7\b\2\2)*\5\n\6\2*\t\3\2\2\2")
        buf.write("+,\5\f\7\2,\13\3\2\2\2-\62\5\16\b\2./\t\2\2\2/\61\5\16")
        buf.write("\b\2\60.\3\2\2\2\61\64\3\2\2\2\62\60\3\2\2\2\62\63\3\2")
        buf.write("\2\2\63\r\3\2\2\2\64\62\3\2\2\2\65:\5\20\t\2\66\67\t\3")
        buf.write("\2\2\679\5\20\t\28\66\3\2\2\29<\3\2\2\2:8\3\2\2\2:;\3")
        buf.write("\2\2\2;\17\3\2\2\2<:\3\2\2\2=>\7\20\2\2>A\5\20\t\2?A\5")
        buf.write("\22\n\2@=\3\2\2\2@?\3\2\2\2A\21\3\2\2\2BI\7\26\2\2CI\5")
        buf.write("\24\13\2DE\7\24\2\2EF\5\n\6\2FG\7\25\2\2GI\3\2\2\2HB\3")
        buf.write("\2\2\2HC\3\2\2\2HD\3\2\2\2I\23\3\2\2\2JK\t\4\2\2K\25\3")
        buf.write("\2\2\2LQ\5\30\r\2MN\7\4\2\2NP\5\30\r\2OM\3\2\2\2PS\3\2")
        buf.write("\2\2QO\3\2\2\2QR\3\2\2\2R\27\3\2\2\2SQ\3\2\2\2TY\5\32")
        buf.write("\16\2UV\7\3\2\2VX\5\32\16\2WU\3\2\2\2X[\3\2\2\2YW\3\2")
        buf.write("\2\2YZ\3\2\2\2Z\31\3\2\2\2[Y\3\2\2\2\\]\5\f\7\2]^\5\34")
        buf.write("\17\2^_\5\f\7\2_e\3\2\2\2`a\7\24\2\2ab\5\26\f\2bc\7\25")
        buf.write("\2\2ce\3\2\2\2d\\\3\2\2\2d`\3\2\2\2e\33\3\2\2\2fg\t\5")
        buf.write("\2\2g\35\3\2\2\2\t\62:@HQYd")
        return buf.getvalue()


class IDLV2ExprParser ( Parser ):

    grammarFileName = "IDLV2Expr.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'and'", "'or'", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "'='", "'=='", "'!='", "'<'", "'<='", 
                     "'>'", "'>='", "'+'", "'-'", "'*'", "'/'", "'%'", "'('", 
                     "')'" ]

    symbolicNames = [ "<INVALID>", "AND", "OR", "ADDRESSING", "COMPUTATIONAL", 
                      "STATE", "ASSIGN", "EQ", "NE", "LT", "LE", "GT", "GE", 
                      "PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "LPAREN", 
                      "RPAREN", "INT", "WORD", "WS", "ERROR_CHAR" ]

    RULE_expression_text = 0
    RULE_constraint_text = 1
    RULE_update_text = 2
    RULE_update = 3
    RULE_expression = 4
    RULE_additive = 5
    RULE_multiplicative = 6
    RULE_unary = 7
    RULE_atom = 8
    RULE_reference = 9
    RULE_condition = 10
    RULE_conjunction = 11
    RULE_comparison = 12
    RULE_compare = 13

    ruleNames =  [ "expression_text", "constraint_text", "update_text", 
                   "update", "expression", "additive", "multiplicative", 
                   "unary", "atom", "reference", "condition", "conjunction", 
                   "comparison", "compare" ]

    EOF = Token.EOF
    AND=1
    OR=2
    ADDRESSING=3
    COMPUTATIONAL=4
    STATE=5
    ASSIGN=6
    EQ=7
    NE=8
    LT=9
    LE=10
    GT=11
    GE=12
    PLUS=13
    MINUS=14
    STAR=15
    SLASH=16
    PERCENT=17
    LPAREN=18
    RPAREN=19
    INT=20
    WORD=21
    WS=22
    ERROR_CHAR=23

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class Expression_textContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ExpressionContext,0)


        def EOF(self):
            return self.getToken(IDLV2ExprParser.EOF, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_expression_text

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression_text" ):
                listener.enterExpression_text(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression_text" ):
                listener.exitExpression_text(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression_text" ):
                return visitor.visitExpression_text(self)
            else:
                return visitor.visitChildren(self)




    def expression_text(self):

        localctx = IDLV2ExprParser.Expression_textContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expression_text)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 28
            self.expression()
            self.state = 29
            self.match(IDLV2ExprParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Constraint_textContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def condition(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ConditionContext,0)


        def EOF(self):
            return self.getToken(IDLV2ExprParser.EOF, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_constraint_text

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstraint_text" ):
                listener.enterConstraint_text(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstraint_text" ):
                listener.exitConstraint_text(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstraint_text" ):
                return visitor.visitConstraint_text(self)
            else:
                return visitor.visitChildren(self)




    def constraint_text(self):

        localctx = IDLV2ExprParser.Constraint_textContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_constraint_text)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 31
            self.condition()
            self.state = 32
            self.match(IDLV2ExprParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Update_textContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def update(self):
            return self.getTypedRuleContext(IDLV2ExprParser.UpdateContext,0)


        def EOF(self):
            return self.getToken(IDLV2ExprParser.EOF, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_update_text

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUpdate_text" ):
                listener.enterUpdate_text(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUpdate_text" ):
                listener.exitUpdate_text(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUpdate_text" ):
                return visitor.visitUpdate_text(self)
            else:
                return visitor.visitChildren(self)




    def update_text(self):

        localctx = IDLV2ExprParser.Update_textContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_update_text)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 34
            self.update()
            self.state = 35
            self.match(IDLV2ExprParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UpdateContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STATE(self):
            return self.getToken(IDLV2ExprParser.STATE, 0)

        def ASSIGN(self):
            return self.getToken(IDLV2ExprParser.ASSIGN, 0)

        def expression(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ExpressionContext,0)


        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_update

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUpdate" ):
                listener.enterUpdate(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUpdate" ):
                listener.exitUpdate(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUpdate" ):
                return visitor.visitUpdate(self)
            else:
                return visitor.visitChildren(self)




    def update(self):

        localctx = IDLV2ExprParser.UpdateContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_update)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 37
            self.match(IDLV2ExprParser.STATE)
            self.state = 38
            self.match(IDLV2ExprParser.ASSIGN)
            self.state = 39
            self.expression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def additive(self):
            return self.getTypedRuleContext(IDLV2ExprParser.AdditiveContext,0)


        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_expression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = IDLV2ExprParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 41
            self.additive()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AdditiveContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def multiplicative(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(IDLV2ExprParser.MultiplicativeContext)
            else:
                return self.getTypedRuleContext(IDLV2ExprParser.MultiplicativeContext,i)


        def PLUS(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.PLUS)
            else:
                return self.getToken(IDLV2ExprParser.PLUS, i)

        def MINUS(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.MINUS)
            else:
                return self.getToken(IDLV2ExprParser.MINUS, i)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_additive

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAdditive" ):
                listener.enterAdditive(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAdditive" ):
                listener.exitAdditive(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAdditive" ):
                return visitor.visitAdditive(self)
            else:
                return visitor.visitChildren(self)




    def additive(self):

        localctx = IDLV2ExprParser.AdditiveContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_additive)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            self.multiplicative()
            self.state = 48
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==IDLV2ExprParser.PLUS or _la==IDLV2ExprParser.MINUS:
                self.state = 44
                _la = self._input.LA(1)
                if not(_la==IDLV2ExprParser.PLUS or _la==IDLV2ExprParser.MINUS):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 45
                self.multiplicative()
                self.state = 50
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MultiplicativeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unary(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(IDLV2ExprParser.UnaryContext)
            else:
                return self.getTypedRuleContext(IDLV2ExprParser.UnaryContext,i)


        def STAR(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.STAR)
            else:
                return self.getToken(IDLV2ExprParser.STAR, i)

        def SLASH(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.SLASH)
            else:
                return self.getToken(IDLV2ExprParser.SLASH, i)

        def PERCENT(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.PERCENT)
            else:
                return self.getToken(IDLV2ExprParser.PERCENT, i)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_multiplicative

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMultiplicative" ):
                listener.enterMultiplicative(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMultiplicative" ):
                listener.exitMultiplicative(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultiplicative" ):
                return visitor.visitMultiplicative(self)
            else:
                return visitor.visitChildren(self)




    def multiplicative(self):

        localctx = IDLV2ExprParser.MultiplicativeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_multiplicative)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 51
            self.unary()
            self.state = 56
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << IDLV2ExprParser.STAR) | (1 << IDLV2ExprParser.SLASH) | (1 << IDLV2ExprParser.PERCENT))) != 0):
                self.state = 52
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << IDLV2ExprParser.STAR) | (1 << IDLV2ExprParser.SLASH) | (1 << IDLV2ExprParser.PERCENT))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 53
                self.unary()
                self.state = 58
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UnaryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MINUS(self):
            return self.getToken(IDLV2ExprParser.MINUS, 0)

        def unary(self):
            return self.getTypedRuleContext(IDLV2ExprParser.UnaryContext,0)


        def atom(self):
            return self.getTypedRuleContext(IDLV2ExprParser.AtomContext,0)


        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_unary

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUnary" ):
                listener.enterUnary(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUnary" ):
                listener.exitUnary(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnary" ):
                return visitor.visitUnary(self)
            else:
                return visitor.visitChildren(self)




    def unary(self):

        localctx = IDLV2ExprParser.UnaryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_unary)
        try:
            self.state = 62
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [IDLV2ExprParser.MINUS]:
                self.enterOuterAlt(localctx, 1)
                self.state = 59
                self.match(IDLV2ExprParser.MINUS)
                self.state = 60
                self.unary()
                pass
            elif token in [IDLV2ExprParser.ADDRESSING, IDLV2ExprParser.COMPUTATIONAL, IDLV2ExprParser.STATE, IDLV2ExprParser.LPAREN, IDLV2ExprParser.INT]:
                self.enterOuterAlt(localctx, 2)
                self.state = 61
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AtomContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(IDLV2ExprParser.INT, 0)

        def reference(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ReferenceContext,0)


        def LPAREN(self):
            return self.getToken(IDLV2ExprParser.LPAREN, 0)

        def expression(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ExpressionContext,0)


        def RPAREN(self):
            return self.getToken(IDLV2ExprParser.RPAREN, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_atom

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAtom" ):
                listener.enterAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAtom" ):
                listener.exitAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtom" ):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)




    def atom(self):

        localctx = IDLV2ExprParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_atom)
        try:
            self.state = 70
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [IDLV2ExprParser.INT]:
                self.enterOuterAlt(localctx, 1)
                self.state = 64
                self.match(IDLV2ExprParser.INT)
                pass
            elif token in [IDLV2ExprParser.ADDRESSING, IDLV2ExprParser.COMPUTATIONAL, IDLV2ExprParser.STATE]:
                self.enterOuterAlt(localctx, 2)
                self.state = 65
                self.reference()
                pass
            elif token in [IDLV2ExprParser.LPAREN]:
                self.enterOuterAlt(localctx, 3)
                self.state = 66
                self.match(IDLV2ExprParser.LPAREN)
                self.state = 67
                self.expression()
                self.state = 68
                self.match(IDLV2ExprParser.RPAREN)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ReferenceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ADDRESSING(self):
            return self.getToken(IDLV2ExprParser.ADDRESSING, 0)

        def COMPUTATIONAL(self):
            return self.getToken(IDLV2ExprParser.COMPUTATIONAL, 0)

        def STATE(self):
            return self.getToken(IDLV2ExprParser.STATE, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_reference

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterReference" ):
                listener.enterReference(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitReference" ):
                listener.exitReference(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitReference" ):
                return visitor.visitReference(self)
            else:
                return visitor.visitChildren(self)




    def reference(self):

        localctx = IDLV2ExprParser.ReferenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_reference)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 72
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << IDLV2ExprParser.ADDRESSING) | (1 << IDLV2ExprParser.COMPUTATIONAL) | (1 << IDLV2ExprParser.STATE))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConditionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def conjunction(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(IDLV2ExprParser.ConjunctionContext)
            else:
                return self.getTypedRuleContext(IDLV2ExprParser.ConjunctionContext,i)


        def OR(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.OR)
            else:
                return self.getToken(IDLV2ExprParser.OR, i)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_condition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCondition" ):
                listener.enterCondition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCondition" ):
                listener.exitCondition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCondition" ):
                return visitor.visitCondition(self)
            else:
                return visitor.visitChildren(self)




    def condition(self):

        localctx = IDLV2ExprParser.ConditionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_condition)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            self.conjunction()
            self.state = 79
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==IDLV2ExprParser.OR:
                self.state = 75
                self.match(IDLV2ExprParser.OR)
                self.state = 76
                self.conjunction()
                self.state = 81
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConjunctionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def comparison(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(IDLV2ExprParser.ComparisonContext)
            else:
                return self.getTypedRuleContext(IDLV2ExprParser.ComparisonContext,i)


        def AND(self, i:int=None):
            if i is None:
                return self.getTokens(IDLV2ExprParser.AND)
            else:
                return self.getToken(IDLV2ExprParser.AND, i)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_conjunction

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConjunction" ):
                listener.enterConjunction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConjunction" ):
                listener.exitConjunction(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConjunction" ):
                return visitor.visitConjunction(self)
            else:
                return visitor.visitChildren(self)




    def conjunction(self):

        localctx = IDLV2ExprParser.ConjunctionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_conjunction)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 82
            self.comparison()
            self.state = 87
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==IDLV2ExprParser.AND:
                self.state = 83
                self.match(IDLV2ExprParser.AND)
                self.state = 84
                self.comparison()
                self.state = 89
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComparisonContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def additive(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(IDLV2ExprParser.AdditiveContext)
            else:
                return self.getTypedRuleContext(IDLV2ExprParser.AdditiveContext,i)


        def compare(self):
            return self.getTypedRuleContext(IDLV2ExprParser.CompareContext,0)


        def LPAREN(self):
            return self.getToken(IDLV2ExprParser.LPAREN, 0)

        def condition(self):
            return self.getTypedRuleContext(IDLV2ExprParser.ConditionContext,0)


        def RPAREN(self):
            return self.getToken(IDLV2ExprParser.RPAREN, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_comparison

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComparison" ):
                listener.enterComparison(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComparison" ):
                listener.exitComparison(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComparison" ):
                return visitor.visitComparison(self)
            else:
                return visitor.visitChildren(self)




    def comparison(self):

        localctx = IDLV2ExprParser.ComparisonContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_comparison)
        try:
            self.state = 98
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,6,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 90
                self.additive()
                self.state = 91
                self.compare()
                self.state = 92
                self.additive()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 94
                self.match(IDLV2ExprParser.LPAREN)
                self.state = 95
                self.condition()
                self.state = 96
                self.match(IDLV2ExprParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CompareContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EQ(self):
            return self.getToken(IDLV2ExprParser.EQ, 0)

        def NE(self):
            return self.getToken(IDLV2ExprParser.NE, 0)

        def LT(self):
            return self.getToken(IDLV2ExprParser.LT, 0)

        def LE(self):
            return self.getToken(IDLV2ExprParser.LE, 0)

        def GT(self):
            return self.getToken(IDLV2ExprParser.GT, 0)

        def GE(self):
            return self.getToken(IDLV2ExprParser.GE, 0)

        def getRuleIndex(self):
            return IDLV2ExprParser.RULE_compare

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompare" ):
                listener.enterCompare(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompare" ):
                listener.exitCompare(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompare" ):
                return visitor.visitCompare(self)
            else:
                return visitor.visitChildren(self)




    def compare(self):

        localctx = IDLV2ExprParser.CompareContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_compare)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 100
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << IDLV2ExprParser.EQ) | (1 << IDLV2ExprParser.NE) | (1 << IDLV2ExprParser.LT) | (1 << IDLV2ExprParser.LE) | (1 << IDLV2ExprParser.GT) | (1 << IDLV2ExprParser.GE))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





