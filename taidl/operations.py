"""What each operation word takes: its operands and its attributes.

XLA-HLO's shape-free checks, operand count and kind and each attribute's name, presence and form,
with StableHLO's dot, pad and transpose_a rules; shapes and element types are not checked here.
"""

import re

from antlr4.Token import CommonToken

from .antlr4 import IDLV2Parser

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

# A fault: its token and its message
Fault = tuple[CommonToken, str]


def check_operations(semantics: IDLV2Parser.ModuleContext) -> Fault | None:
    """The first line that breaks its word's row, or names a value no earlier line defines."""
    defined = set()
    for line in semantics.instruction():
        word = line.OPERATION().getSymbol()
        takes, attributes = OPERATIONS[word.text]
        operands = line.operands().operand() if line.operands() else []
        given = line.attributes().attribute() if line.attributes() else []
        fault = operand_fault(word, takes, operands, defined) or attribute_fault(
            word, attributes, given
        )
        if fault:
            return fault
        name = line.IDENTIFIER().getSymbol()
        if name.text in defined:
            return name, f"'{name.text}' is defined twice"
        defined.add(name.text)
    return None


def operand_fault(word: CommonToken, takes, operands: list, defined: set[str]) -> Fault | None:
    """A line's operands against its row: their count, what each is, and where each is defined."""
    found = len(operands)
    if takes in (NUMBER_OF_INPUT, LITERAL):
        if found != 1:
            return word, f'{word.text} takes 1 operand, found {found}'
        value = operands[0].value()
        if takes == NUMBER_OF_INPUT:
            fits = value.INT() is not None
        else:
            fits = value.IDENTIFIER() is None or value.getText() in ('true', 'false')
        return (
            None if fits else (value.start, f"{word.text} takes {takes}, found '{value.getText()}'")
        )
    least, most = takes if isinstance(takes, tuple) else (takes, takes)
    if most is None and found < least:
        return word, f'{word.text} takes {least} or more operands, found {found}'
    if most is not None and found != least:
        plural = '' if least == 1 else 's'
        return word, f'{word.text} takes {least} operand{plural}, found {found}'
    for operand in operands:
        name = operand.getText()
        if not name.startswith('%'):
            return operand.start, f"{word.text} takes values as operands, found '{name}'"
        if name not in defined:
            return operand.start, f"'{name}' is defined by no earlier line"
    return None


def attribute_fault(word: CommonToken, takes: dict, attributes: list) -> Fault | None:
    """A line's attributes against its row: unknown, given twice, malformed, then missing."""
    seen = set()
    for attribute in attributes:
        name = attribute.name().getText()
        if name not in takes:
            known = ', '.join(takes) or 'none'
            return attribute.start, f"{word.text} has no attribute '{name}': it takes {known}"
        if name in seen:
            return attribute.start, f"{word.text} is given '{name}' twice"
        seen.add(name)
        form = takes[name][0]
        value = attribute.attribute_value()
        if not fits(form, value):
            found = value.getText()
            return value.start, f"'{name}' of {word.text} takes {described(form)}, found '{found}'"
    for name, (_, required) in takes.items():
        if required and name not in seen:
            return word, f"{word.text} needs the attribute '{name}'"
    return None


def fits(form, given: IDLV2Parser.Attribute_valueContext) -> bool:
    """Whether an attribute's value has the form the table gives it."""
    value, braces, ranges = given.value(), given.brace_list(), given.slice_list()
    if form == INT:
        return value is not None and is_integer(value)
    if form in (INTS, ONE_INT):
        if braces is None or not all(is_integer(entry) for entry in braces.value()):
            return False
        return form == INTS or len(braces.value()) == 1
    if form == RANGES:
        return ranges is not None and all(is_integer(bound) for bound in ranges.value())
    if form == BOOL:
        return value is not None and value.getText() in ('true', 'false')
    if form == NUMBER:
        return value is not None and (value.INT() or value.NUMBER()) is not None
    # A word of a closed set
    return value is not None and value.IDENTIFIER() is not None and value.getText() in form


def is_integer(value: IDLV2Parser.ValueContext) -> bool:
    """An integer literal of either sign, or an expression."""
    if value.INT() or value.EXPRESSION():
        return True
    return value.NUMBER() is not None and re.fullmatch(r'-?[0-9]+', value.getText()) is not None


def described(form) -> str:
    """A form as a message names it."""
    return form if isinstance(form, str) else 'one of ' + ', '.join(form)
