"""Tests for the semantics grammar"""

import os
import re

import pytest
import taidl.antlr4
from taidl import Accelerator

GRAMMAR = os.path.join(os.path.dirname(taidl.antlr4.__file__), 'IDLV2.g4')

acc = Accelerator('Grammar')


def parse(semantics):
    instr = acc.add_instruction('t', [], [])
    instr.add_semantics(semantics)
    return instr.instr_semantics_ast


def spec(*lines):
    return (
        'ENTRY t {\n    %In1 = f32[4] parameter(0);\n'
        + ''.join(f'    {line}\n' for line in lines)
        + '}\n'
    )


def lexed(rule):
    """The words a lexer rule of the grammar file lists."""
    with open(GRAMMAR) as file:
        text = re.sub(r'//.*', '', file.read())
    body = re.search(rf'^{rule}\s*:(.*?);', text, re.MULTILINE | re.DOTALL).group(1)
    return re.findall(r"'([^']+)'", body)


# The operation words by family
FAMILIES = {
    'inputs and constants': 'parameter constant iota',
    'elementwise arithmetic': 'abs negate sign add subtract multiply divide maximum minimum power'
    ' sqrt rsqrt exp exponential log log_plus_one logistic tanh sine round_nearest_even',
    'logic and shifts': 'and or xor shift_left shift_right_logical shift_right_arithmetic',
    'comparison and selection': 'compare select select_lt select_eq_var clamp',
    'type conversion': 'convert bitcast_convert',
    'shape and movement': 'reshape transpose broadcast concatenate slice dynamic_update_slice'
    ' gather copy',
    'contraction': 'dot',
    'reduction': 'reduce reduce_add reduce_max reduce_min reduce_and reduce_or',
}
OPERATIONS = ' '.join(FAMILIES.values()).split()

TYPES = ['s8', 's16', 's32', 'u8', 'u16', 'u32', 'f32', 'f16', 'bf16', 'pred']


class TestWords:
    def test_lists_match_grammar(self):
        assert sorted(lexed('OPERATION')) == sorted(OPERATIONS)
        assert sorted(lexed('TYPE')) == sorted(TYPES)

    @pytest.mark.parametrize('op', OPERATIONS)
    def test_operation(self, op):
        tree = parse(spec(f'ROOT %Out0 = f32[4] {op}(%In1);'))
        assert tree.instruction(1).OPERATION().getText() == op

    @pytest.mark.parametrize('op', ['frobnicate', 'log-plus-one'], ids=['unknown', 'hyphenated'])
    def test_word_outside_the_list_fails(self, op):
        with pytest.raises(SyntaxError):
            parse(spec(f'ROOT %Out0 = f32[4] {op}(%In1);'))

    def test_type_outside_the_list_fails(self):
        with pytest.raises(SyntaxError):
            parse(spec('ROOT %Out0 = f64[4] convert(%In1);'))

    @pytest.mark.parametrize('typ', TYPES)
    def test_type(self, typ):
        tree = parse(spec(f'ROOT %Out0 = {typ}[4] convert(%In1);'))
        assert tree.instruction(1).result_type().TYPE().getText() == typ
