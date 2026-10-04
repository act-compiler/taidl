grammar IDLV2;

// === Parser Rules ===

module         : ENTRY IDENTIFIER LBRACE instruction+ RBRACE ;

instruction    : ROOT? IDENTIFIER EQUAL result_type OPERATION LPAREN operands? RPAREN attributes? SEMICOLON? ;

result_type    : TYPE LBRACKET shape RBRACKET ;

operands       : operand (COMMA operand)* ;
operand        : value ;

attributes     : COMMA attribute (COMMA attribute)* ;
attribute      : IDENTIFIER EQUAL attributeValue ;

attributeValue : braceList | sliceList | value ;
braceList      : LBRACE (value (COMMA value)*)? RBRACE ;
sliceList      : LBRACE ( LBRACKET value COLON value (COLON value)? RBRACKET (COMMA LBRACKET value COLON value (COLON value)? RBRACKET)*)? RBRACE ;

shape          : value (COMMA value)* ;

value          : INT | IDENTIFIER | EXPRESSION ;

// === Lexer Rules ===

// Keywords
ENTRY    : 'ENTRY' ;
ROOT     : 'ROOT' ;

// Element types, spelled as XLA-HLO text spells them
TYPE     : 'pred' | 's8' | 's16' | 's32' | 'u8' | 'u16' | 'u32' | 'f16' | 'bf16' | 'f32' ;

// Operations as XLA-HLO names them; reduce_<reducer> is TAIDL's own
OPERATION
    // Inputs and constants
    : 'parameter' | 'constant' | 'iota'
    // Elementwise arithmetic
    | 'abs' | 'negate' | 'sign' | 'add' | 'subtract' | 'multiply' | 'divide'
    | 'maximum' | 'minimum' | 'power' | 'sqrt' | 'rsqrt' | 'exponential'
    | 'log' | 'log_plus_one' | 'logistic' | 'tanh' | 'sine' | 'round_nearest_even'
    // Logic and shifts
    | 'and' | 'or' | 'xor' | 'shift_left' | 'shift_right_logical' | 'shift_right_arithmetic'
    // Comparison and selection
    | 'compare' | 'select' | 'clamp'
    // Type conversion
    | 'convert' | 'bitcast_convert'
    // Shape and movement
    | 'reshape' | 'transpose' | 'broadcast' | 'concatenate' | 'slice'
    | 'dynamic_update_slice' | 'gather' | 'copy'
    // Contraction
    | 'dot'
    // Reduction
    | 'reduce_add' | 'reduce_max' | 'reduce_min' | 'reduce_and' | 'reduce_or'
    ;

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
