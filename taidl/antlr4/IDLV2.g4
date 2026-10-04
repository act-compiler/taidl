grammar IDLV2;

// === Parser Rules ===

module       : ENTRY IDENTIFIER LBRACE instruction+ RBRACE ;

instruction  : (ROOT)? IDENTIFIER EQUAL result_type OPERATION LPAREN operands? RPAREN attributes? SEMICOLON? ;

result_type       : TYPE LBRACKET shape RBRACKET ;

operands     : operand (COMMA operand)* ;
operand      : value ;

attributes   : COMMA attribute (COMMA attribute)* ;
attribute    : IDENTIFIER EQUAL attributeValue ;

attributeValue : braceList | sliceList | value ;
braceList    : LBRACE (value (COMMA value)*)? RBRACE ;
sliceList    : LBRACE ( LBRACKET value COLON value (COLON value)? RBRACKET (COMMA LBRACKET value COLON value (COLON value)? RBRACKET)*)? RBRACE ;

shape : (value) (COMMA (value))*;

value : INT | IDENTIFIER | EXPRESSION;

// === Lexer Rules ===

// Keywords
ENTRY    : 'ENTRY' ;
ROOT     : 'ROOT' ;

// Element types, spelled as XLA-HLO text spells them
TYPE     : 's8' | 's16' | 's32' | 'u8' | 'u16' | 'u32' | 'f32' | 'f16' | 'bf16' | 'pred' ;

// Operations as XLA-HLO names them; reduce_<reducer> is TAIDL's own
OPERATION : 'reshape' | 'convert' | 'copy' | 'concatenate' | 'bitcast_convert'
          | 'transpose' | 'slice' | 'dot' | 'constant' | 'broadcast' | 'maximum'
          | 'minimum' | 'xor' | 'add'
          | 'dynamic_update_slice' | 'subtract' | 'multiply' | 'divide'
          | 'parameter' | 'reduce_add' | 'exponential'
          | 'reduce_max' | 'reduce_min' | 'reduce_and' | 'reduce_or' | 'gather' | 'iota'
          | 'abs' | 'negate' | 'sign' | 'sqrt' | 'rsqrt' | 'log' | 'log_plus_one' | 'logistic'
          | 'tanh' | 'sine' | 'round_nearest_even' | 'power' | 'clamp' | 'compare' | 'select'
          | 'and' | 'or' | 'shift_left' | 'shift_right_logical' | 'shift_right_arithmetic';

// Symbols
EQUAL    : '=' ;
LPAREN   : '(' ;
RPAREN   : ')' ;
LBRACE   : '{' ;
RBRACE   : '}' ;
LBRACKET : '[' ;
RBRACKET : ']' ;
COLON    : ':' ;
SEMICOLON: ';' ;
COMMA    : ',' ;

// Tokens
INT        : [0-9]+ ;
EXPRESSION : '`' (~'`')* '`' ;
IDENTIFIER : '%'?[a-zA-Z_@][a-zA-Z0-9_.@]* ;
WS         : [ \t\r\n]+ -> skip ;
