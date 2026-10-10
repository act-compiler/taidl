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
        'ENTRY {\n    %In0 = f32[4] parameter(0);\n'
        + ''.join(f'    {line}\n' for line in lines)
        + '}\n'
    )


def lexed(rule):
    """The words a lexer rule of the grammar file lists."""
    with open(GRAMMAR) as file:
        text = re.sub(r'//.*', '', file.read())
    body = re.search(rf'^{rule}\s*:(.*?);', text, re.MULTILINE | re.DOTALL).group(1)
    return re.findall(r"'([^']+)'", body)


COPY = 'ROOT %Out0 = f32[4] copy(%In0);'


class TestStrict:
    def test_clean_spec_parses(self):
        tree = parse(spec('ROOT %Out0 = f32[4] copy(%In0);'))
        assert tree.instruction(1).OPERATION().getText() == 'copy'

    @pytest.mark.parametrize(
        'line',
        [
            'ROOT %Out0 = f32[4] add(%In0, -%In0);',
            'ROOT %Out0 = f32[4] copy($%In0);',
            'ROOT %Out0 = f32[4] copy(%In0);!',
        ],
        ids=['sign_alone', 'in_operands', 'after_semicolon'],
    )
    def test_unknown_character_fails(self, line):
        with pytest.raises(SyntaxError):
            parse(spec(line))

    @pytest.mark.parametrize(
        'text, where',
        [
            ('$' + spec(COPY), 'line 1, column 1'),
            (spec('ROOT %Out0 = f32[4] add(%In0, -%In0);'), 'line 3, column 35'),
            (
                spec('%a = f32[`@c.n *\n 2`] copy(%In0);', 'ROOT %Out0 = f32[4] copy($);'),
                'line 5, column 30',
            ),
            (spec(COPY) + '$', 'line 5, column 1'),
            (spec(COPY)[:-2], 'line 4, column 1'),
        ],
        ids=[
            'first_character',
            'mid_line',
            'after_a_two_line_expression',
            'after_the_module',
            'end_of_text',
        ],
    )
    def test_error_names_line_and_column(self, text, where, capsys):
        with pytest.raises(SyntaxError, match=f't: semantics {where}: '):
            parse(text)
        # The error is raised, never printed
        assert capsys.readouterr() == ('', '')

    def test_text_after_module_fails(self):
        with pytest.raises(SyntaxError):
            parse(spec('ROOT %Out0 = f32[4] copy(%In0);') + '}')

    @pytest.mark.parametrize(
        'text', ['', '  \n', 'ENTRY {\n}\n'], ids=['empty', 'blank', 'no_line']
    )
    def test_semantics_with_no_line_fails(self, text):
        with pytest.raises(SyntaxError, match='t: semantics line'):
            parse(text)


class TestComments:
    def test_comment_skipped(self):
        text = '// the copy\n' + spec('// its one line', 'ROOT %Out0 = f32[4] copy(%In0); // done')
        tree = parse(text)
        assert [line.OPERATION().getText() for line in tree.instruction()] == ['parameter', 'copy']

    def test_floor_division_stays_in_an_expression(self):
        tree = parse(spec('ROOT %Out0 = f32[`@c.n // 2`] copy(%In0);'))
        assert tree.instruction(1).result_type().shape().getText() == '`@c.n // 2`'


class TestRoot:
    @pytest.mark.parametrize(
        'lines, found',
        [
            (['%Out0 = f32[4] copy(%In0);'], 0),
            (['ROOT %a = f32[4] copy(%In0);', 'ROOT %Out0 = f32[4] copy(%a);'], 2),
        ],
        ids=['none', 'two'],
    )
    def test_root_count_fails(self, lines, found):
        with pytest.raises(
            SyntaxError, match=f't: semantics needs exactly one ROOT, found {found}'
        ):
            parse(spec(*lines))

    def test_root_on_the_last_of_several_outputs(self):
        tree = parse(
            spec(
                '%Out1 = f32[4] negate(%In0);',
                '%Out0 = f32[4] copy(%In0);',
                'ROOT %Out2 = f32[4] add(%Out0, %Out1);',
            )
        )
        assert tree.instruction(3).ROOT() is not None

    @pytest.mark.parametrize(
        'lines, message',
        [
            (
                ['%Out0 = f32[4] copy(%In0);', 'ROOT %a = f32[4] negate(%Out0);'],
                "line 4, column 5: ROOT is on '%a', not on the last output '%Out0'",
            ),
            (
                ['ROOT %Out0 = f32[4] copy(%In0);', '%Out1 = f32[4] negate(%In0);'],
                "line 3, column 5: ROOT is on '%Out0', not on the last output '%Out1'",
            ),
        ],
        ids=['not_an_output', 'not_the_last_output'],
    )
    def test_root_elsewhere_fails(self, lines, message):
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics {message}')):
            parse(spec(*lines))


class TestInputs:
    def test_inputs_count_from_zero(self):
        tree = parse(spec('%In1 = f32[4] parameter(1);', 'ROOT %Out0 = f32[4] add(%In0, %In1);'))
        assert [line.IDENTIFIER().getText() for line in tree.instruction()][:2] == ['%In0', '%In1']

    @pytest.mark.parametrize(
        'lines, message',
        [
            (
                ['%In2 = f32[4] parameter(1);', 'ROOT %Out0 = f32[4] add(%In0, %In2);'],
                "line 3, column 5: parameter(1) declares '%In1', not '%In2'",
            ),
            (
                ['%In1 = f32[4] negate(%In0);', 'ROOT %Out0 = f32[4] add(%In0, %In1);'],
                "line 3, column 5: '%In1' is declared by parameter(1), not by negate",
            ),
            (
                ['%In00 = f32[4] parameter(00);', 'ROOT %Out0 = f32[4] add(%In0, %In00);'],
                "line 3, column 5: parameter(00) declares '%In0', not '%In00'",
            ),
            (
                ['%In1 = f32[4] parameter(%In0);', 'ROOT %Out0 = f32[4] add(%In0, %In1);'],
                "line 3, column 19: parameter(%In0) needs one integer, the input's number",
            ),
            (
                ['%In1 = f32[4] parameter(0,1);', 'ROOT %Out0 = f32[4] add(%In0, %In1);'],
                "line 3, column 19: parameter(0,1) needs one integer, the input's number",
            ),
        ],
        ids=[
            'parameter_misnamed',
            'input_name_not_a_parameter',
            'parameter_number_with_leading_zero',
            'parameter_operand_not_an_integer',
            'parameter_of_two_operands',
        ],
    )
    def test_input_named_otherwise_fails(self, lines, message):
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics {message}')):
            parse(spec(*lines))


# The operation words by family
FAMILIES = {
    'inputs and constants': 'parameter constant iota',
    'elementwise arithmetic': 'abs negate sign add subtract multiply mulhi divide remainder'
    ' maximum minimum power sqrt rsqrt cbrt',
    'transcendental functions': 'exponential exponential_minus_one log log_plus_one logistic erf'
    ' sine cosine tan asin acos atan2 sinh cosh tanh asinh acosh atanh',
    'rounding': 'floor ceil round_nearest_afz round_nearest_even',
    'logic and bits': 'and or xor not shift_left shift_right_logical shift_right_arithmetic'
    ' popcnt count_leading_zeros',
    'comparison and selection': 'compare select clamp is_finite',
    'type conversion': 'convert bitcast_convert reduce_precision',
    'shape and movement': 'reshape transpose broadcast concatenate pad reverse slice'
    ' dynamic_slice dynamic_update_slice gather copy',
    'linear algebra': 'dot cholesky triangular_solve',
    'normalization': 'batch_norm_inference',
    'reduction': 'reduce_add reduce_multiply reduce_max reduce_min reduce_and reduce_or reduce_xor',
}
OPERATIONS = ' '.join(FAMILIES.values()).split()

TYPES = 'pred s2 s4 s8 s16 s32 s64 u2 u4 u8 u16 u32 u64 f8e4m3fn f8e5m2 f16 bf16 f32 f64'.split()


class TestWords:
    def test_lists_match_grammar(self):
        assert sorted(lexed('OPERATION')) == sorted(OPERATIONS)
        assert sorted(lexed('TYPE')) == sorted(TYPES)

    @pytest.mark.parametrize('op', OPERATIONS)
    def test_operation(self, op):
        # parameter declares an input; any other word computes the output
        if op == 'parameter':
            lines = ['%In1 = f32[4] parameter(1);', COPY]
        else:
            lines = [f'ROOT %Out0 = f32[4] {op}(%In0);']
        tree = parse(spec(*lines))
        assert tree.instruction(1).OPERATION().getText() == op

    @pytest.mark.parametrize('op', ['frobnicate', 'log-plus-one'], ids=['unknown', 'hyphenated'])
    def test_word_outside_the_list_fails(self, op):
        with pytest.raises(SyntaxError):
            parse(spec(f'ROOT %Out0 = f32[4] {op}(%In0);'))

    @pytest.mark.parametrize(
        'typ', ['c64', 'f8e4m3', 'f8e5m2fnuz'], ids=['unlisted', 'shorter_name', 'longer_name']
    )
    def test_type_outside_the_list_fails(self, typ):
        # The whole word is refused, where it starts
        with pytest.raises(SyntaxError, match='t: semantics line 3, column 18: '):
            parse(spec(f'ROOT %Out0 = {typ}[4] convert(%In0);'))

    @pytest.mark.parametrize('typ', TYPES)
    def test_type(self, typ):
        tree = parse(spec(f'ROOT %Out0 = {typ}[4] convert(%In0);'))
        assert tree.instruction(1).result_type().TYPE().getText() == typ


class TestLiterals:
    @pytest.mark.parametrize(
        'text', ['-1', '-0', '0.5', '-2.5', '1e-3', '-6.25E+2', 'inf', '-inf', 'nan']
    )
    def test_number_operand(self, text):
        tree = parse(spec(f'ROOT %Out0 = f32[1] constant({text});'))
        value = tree.instruction(1).operands().operand(0).value()
        assert value.NUMBER().getText() == text

    @pytest.mark.parametrize('text', ['info', 'nano', 'inf_x', '%inf'])
    def test_longer_word_stays_identifier(self, text):
        tree = parse(spec(f'ROOT %Out0 = f32[1] constant({text});'))
        value = tree.instruction(1).operands().operand(0).value()
        assert value.IDENTIFIER().getText() == text

    def test_integer_stays_int(self):
        tree = parse(spec('ROOT %Out0 = s32[1] constant(7);'))
        value = tree.instruction(1).operands().operand(0).value()
        assert value.INT().getText() == '7'
        assert value.NUMBER() is None

    def test_number_attribute(self):
        tree = parse(spec('ROOT %Out0 = f32[4] power(%In0), exponent=-0.5;'))
        value = tree.instruction(1).attributes().attribute(0).attribute_value().value()
        assert value.NUMBER().getText() == '-0.5'

    def test_number_brace_list(self):
        tree = parse(spec('ROOT %Out0 = f32[4] constant(), values={-1, 0.5, 2};'))
        attribute = tree.instruction(1).attributes().attribute(0)
        values = attribute.attribute_value().brace_list().value()
        assert [v.getText() for v in values] == ['-1', '0.5', '2']
        assert [v.NUMBER() is not None for v in values] == [True, True, False]


class TestShapes:
    def test_rank0_result(self):
        tree = parse(spec('ROOT %Out0 = f32[] constant(-1);'))
        result = tree.instruction(1).result_type()
        assert result.TYPE().getText() == 'f32'
        assert result.shape() is None

    def test_ranked_result(self):
        tree = parse(spec('ROOT %Out0 = f32[`@c.n`,4] broadcast(%In0), dimensions={1};'))
        assert tree.instruction(1).result_type().shape().getText() == '`@c.n`,4'


class TestEntry:
    def test_name_fails(self):
        with pytest.raises(
            SyntaxError, match="t: semantics line 1, column 7: extraneous input 't'"
        ):
            parse('ENTRY t {\n    %In0 = f32[4] parameter(0);\n    ' + COPY + '\n}\n')


class TestAttributes:
    def test_identifier_name(self):
        tree = parse(spec('ROOT %Out0 = f32[4] broadcast(%In0), dimensions={0};'))
        attribute = tree.instruction(1).attributes().attribute(0)
        assert attribute.name().getText() == 'dimensions'
        assert attribute.name().IDENTIFIER() is not None

    @pytest.mark.parametrize('op', ['slice', 'select', 'dot'])
    def test_operation_name(self, op):
        tree = parse(spec(f'ROOT %Out0 = f32[4] copy(%In0), {op}=1;'))
        attribute = tree.instruction(1).attributes().attribute(0)
        assert attribute.name().getText() == op
        assert attribute.name().OPERATION() is not None

    def test_slice_list(self):
        tree = parse(spec('ROOT %Out0 = f32[2] slice(%In0), slice={[0:4:2]};'))
        attribute = tree.instruction(1).attributes().attribute(0)
        assert attribute.name().getText() == 'slice'
        assert attribute.attribute_value().slice_list().getText() == '{[0:4:2]}'
