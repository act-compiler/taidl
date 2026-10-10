"""What each operation word takes: its operands and its attributes.

XLA-HLO's shape-free checks, operand count and kind and each attribute's name, presence and form,
with StableHLO's dot, pad and transpose_a rules; shapes and element types are not checked here.
"""

# The form of an attribute's value
INT = 'an integer'
INTS = 'a list of integers'
ONE_INT = 'a list of one integer'
RANGES = 'a list of ranges'
BOOL = 'true or false'
NUMBER = 'a number'
# A closed set of words, as a tuple
DIRECTIONS = ('EQ', 'NE', 'GE', 'GT', 'LE', 'LT')
COMPARE_TYPES = ('FLOAT', 'TOTALORDER', 'SIGNED', 'UNSIGNED')
TRANSPOSES = ('NO_TRANSPOSE', 'TRANSPOSE', 'ADJOINT')

# The operand of parameter and constant
NUMBER_OF_INPUT = 'the number of an input'
LITERAL = 'a number, true, false or an expression'

# Whether a line must give the attribute
REQUIRED, OPTIONAL = True, False


def at_least(count: int) -> tuple[int, None]:
    """An operand count with no upper end."""
    return (count, None)


DIMENSIONS = {'dimensions': (INTS, REQUIRED)}

# word: (operands, {attribute: (form, required)})
OPERATIONS = {
    # Inputs and constants
    'parameter': (NUMBER_OF_INPUT, {}),
    'constant': (LITERAL, {}),
    'iota': (0, {'iota_dimension': (INT, REQUIRED)}),
    # Elementwise arithmetic
    'abs': (1, {}),
    'negate': (1, {}),
    'sign': (1, {}),
    'add': (2, {}),
    'subtract': (2, {}),
    'multiply': (2, {}),
    'mulhi': (2, {}),
    'divide': (2, {}),
    'remainder': (2, {}),
    'maximum': (2, {}),
    'minimum': (2, {}),
    'power': (2, {}),
    'sqrt': (1, {}),
    'rsqrt': (1, {}),
    'cbrt': (1, {}),
    # Transcendental functions
    'exponential': (1, {}),
    'exponential_minus_one': (1, {}),
    'log': (1, {}),
    'log_plus_one': (1, {}),
    'logistic': (1, {}),
    'erf': (1, {}),
    'sine': (1, {}),
    'cosine': (1, {}),
    'tan': (1, {}),
    'asin': (1, {}),
    'acos': (1, {}),
    'atan2': (2, {}),
    'sinh': (1, {}),
    'cosh': (1, {}),
    'tanh': (1, {}),
    'asinh': (1, {}),
    'acosh': (1, {}),
    'atanh': (1, {}),
    # Rounding
    'floor': (1, {}),
    'ceil': (1, {}),
    'round_nearest_afz': (1, {}),
    'round_nearest_even': (1, {}),
    # Logic and bits
    'and': (2, {}),
    'or': (2, {}),
    'xor': (2, {}),
    'not': (1, {}),
    'shift_left': (2, {}),
    'shift_right_logical': (2, {}),
    'shift_right_arithmetic': (2, {}),
    'popcnt': (1, {}),
    'count_leading_zeros': (1, {}),
    # Comparison and selection
    'compare': (2, {'direction': (DIRECTIONS, REQUIRED), 'type': (COMPARE_TYPES, OPTIONAL)}),
    'select': (3, {}),
    'clamp': (3, {}),
    'is_finite': (1, {}),
    # Type conversion
    'convert': (1, {}),
    'bitcast_convert': (1, {}),
    'reduce_precision': (1, {'exponent_bits': (INT, REQUIRED), 'mantissa_bits': (INT, REQUIRED)}),
    # Shape and movement
    'reshape': (1, {}),
    'transpose': (1, DIMENSIONS),
    'broadcast': (1, DIMENSIONS),
    'concatenate': (at_least(1), {'dimensions': (ONE_INT, REQUIRED)}),
    'pad': (
        2,
        {
            'edge_padding_low': (INTS, REQUIRED),
            'edge_padding_high': (INTS, REQUIRED),
            'interior_padding': (INTS, REQUIRED),
        },
    ),
    'reverse': (1, DIMENSIONS),
    'slice': (1, {'slice': (RANGES, REQUIRED)}),
    'dynamic_slice': (at_least(1), {'dynamic_slice_sizes': (INTS, REQUIRED)}),
    'dynamic_update_slice': (at_least(2), {}),
    'gather': (
        2,
        {
            'offset_dims': (INTS, REQUIRED),
            'collapsed_slice_dims': (INTS, REQUIRED),
            'start_index_map': (INTS, REQUIRED),
            'index_vector_dim': (INT, REQUIRED),
            'slice_sizes': (INTS, REQUIRED),
            'operand_batching_dims': (INTS, OPTIONAL),
            'start_indices_batching_dims': (INTS, OPTIONAL),
        },
    ),
    'copy': (1, {}),
    # Linear algebra
    'dot': (
        2,
        {
            'lhs_batch_dims': (INTS, OPTIONAL),
            'lhs_contracting_dims': (INTS, REQUIRED),
            'rhs_batch_dims': (INTS, OPTIONAL),
            'rhs_contracting_dims': (INTS, REQUIRED),
        },
    ),
    'cholesky': (1, {'lower': (BOOL, OPTIONAL)}),
    'triangular_solve': (
        2,
        {
            'left_side': (BOOL, OPTIONAL),
            'lower': (BOOL, OPTIONAL),
            'unit_diagonal': (BOOL, OPTIONAL),
            'transpose_a': (TRANSPOSES, REQUIRED),
        },
    ),
    # Normalization
    'batch_norm_inference': (5, {'epsilon': (NUMBER, REQUIRED), 'feature_index': (INT, REQUIRED)}),
    # Reduction
    'reduce_add': (1, DIMENSIONS),
    'reduce_multiply': (1, DIMENSIONS),
    'reduce_max': (1, DIMENSIONS),
    'reduce_min': (1, DIMENSIONS),
    'reduce_and': (1, DIMENSIONS),
    'reduce_or': (1, DIMENSIONS),
    'reduce_xor': (1, DIMENSIONS),
}
