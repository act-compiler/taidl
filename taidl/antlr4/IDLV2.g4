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
    | 'abs' | 'negate' | 'sign' | 'add' | 'subtract' | 'multiply' | 'mulhi' | 'divide'
    | 'remainder' | 'maximum' | 'minimum' | 'power' | 'sqrt' | 'rsqrt' | 'cbrt'
    // Transcendental functions
    | 'exponential' | 'exponential_minus_one' | 'log' | 'log_plus_one' | 'logistic' | 'erf'
    | 'sine' | 'cosine' | 'tan' | 'asin' | 'acos' | 'atan2'
    | 'sinh' | 'cosh' | 'tanh' | 'asinh' | 'acosh' | 'atanh'
    // Rounding
    | 'floor' | 'ceil' | 'round_nearest_afz' | 'round_nearest_even'
    // Logic and bits
    | 'and' | 'or' | 'xor' | 'not' | 'shift_left' | 'shift_right_logical' | 'shift_right_arithmetic'
    | 'popcnt' | 'count_leading_zeros'
    // Comparison and selection
    | 'compare' | 'select' | 'clamp' | 'is_finite'
    // Type conversion
    | 'convert' | 'bitcast_convert' | 'reduce_precision'
    // Shape and movement
    | 'reshape' | 'transpose' | 'broadcast' | 'concatenate' | 'pad' | 'reverse' | 'slice'
    | 'dynamic_slice' | 'dynamic_update_slice' | 'gather' | 'copy'
    // Linear algebra
    | 'dot' | 'cholesky' | 'triangular_solve'
    // Normalization
    | 'batch_norm_inference'
    // Reduction
    | 'reduce_add' | 'reduce_multiply' | 'reduce_max' | 'reduce_min'
    | 'reduce_and' | 'reduce_or' | 'reduce_xor'
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
