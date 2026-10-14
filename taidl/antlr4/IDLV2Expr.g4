grammar IDLV2Expr;

// === Parser Rules: instruction.py picks each place's entry rule ===

// One entry per place: a value, a constraint, an update
expression_text : expression EOF ;
constraint_text : condition EOF ;
update_text     : update EOF ;

// A state variable takes a value
update          : STATE ASSIGN expression ;

// A value: an integer, by rising precedence
expression      : additive ;
additive        : multiplicative ((PLUS | MINUS) multiplicative)* ;
multiplicative  : unary ((STAR | SLASH | PERCENT) unary)* ;
unary           : MINUS unary | atom ;
atom            : INT | reference | LPAREN expression RPAREN ;
reference       : ADDRESSING | COMPUTATIONAL | STATE ;

// A condition: true or false, by rising precedence
condition       : conjunction (OR conjunction)* ;
conjunction     : comparison (AND comparison)* ;
comparison      : additive compare additive | LPAREN condition RPAREN ;
compare         : EQ | NE | LT | LE | GT | GE ;

// === Lexer Rules ===

// Keywords
AND : 'and' ;
OR  : 'or' ;

// References: an addressing attribute, a computational attribute, a state variable
ADDRESSING    : '@a.' NAME ;
COMPUTATIONAL : '@c.' NAME ;
STATE         : '@s.' NAME ;

// Assignment
ASSIGN : '=' ;

// Comparison
EQ : '==' ;
NE : '!=' ;
LT : '<' ;
LE : '<=' ;
GT : '>' ;
GE : '>=' ;

// Arithmetic
PLUS    : '+' ;
MINUS   : '-' ;
STAR    : '*' ;
SLASH   : '/' ;
PERCENT : '%' ;
LPAREN  : '(' ;
RPAREN  : ')' ;

// Tokens
INT  : '0' | [1-9] [0-9]* ;
// A bare word, which no parser rule accepts
WORD : NAME ;
WS   : [ \t\r\n]+ -> skip ;
// Any other character, which no parser rule accepts
ERROR_CHAR : . ;

fragment NAME : [a-zA-Z_] [a-zA-Z0-9_]* ;
