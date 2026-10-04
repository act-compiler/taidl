"""Tests for the semantics grammar"""

import os
import re

import pytest
from antlr4 import InputStream
import taidl.antlr4
from taidl import Accelerator
from taidl.antlr4 import IDLV2Lexer
from taidl.operations import (
    BOOL,
    INT,
    INTS,
    LITERAL,
    NUMBER,
    NUMBER_OF_INPUT,
    ONE_INT,
    OPERATIONS,
    RANGES,
)

GRAMMAR = os.path.join(os.path.dirname(taidl.antlr4.__file__), 'IDLV2.g4')
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')

acc = Accelerator('Grammar')


def parse(semantics):
    instr = acc.add_instruction('t', ['n'], [])
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

    @pytest.mark.parametrize(
        'line',
        [
            'ROOT %Out0 = s32[] constant(@c.n);',
            'ROOT %Out0 = f32[4] broadcast(%In0), dimensions={@c.n};',
            'ROOT %Out0 = f32[4] copy(%In0), n=@s.mode;',
        ],
        ids=['operand', 'brace_list', 'attribute'],
    )
    def test_reference_outside_backticks_fails(self, line):
        with pytest.raises(SyntaxError, match='t: semantics line 3, column .*@'):
            parse(spec(line))

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

    def test_double_slash_in_an_expression_is_no_comment(self):
        # The expression grammar refuses the second slash
        message = "t: semantics line 3, column 29: extraneous input '/' expecting"
        with pytest.raises(SyntaxError, match=re.escape(message)):
            parse(spec('ROOT %Out0 = f32[`@c.n // 2`] copy(%In0);'))


class TestValueNames:
    def test_name_without_percent_fails(self):
        message = "t: semantics line 3, column 10: value name 'Out0' has no leading '%'"
        with pytest.raises(SyntaxError, match=message):
            parse(spec('ROOT Out0 = f32[4] copy(%In0);'))

    def test_bare_word_operand_parses(self):
        tree = parse(spec('ROOT %Out0 = pred[] constant(true);'))
        assert tree.instruction(1).operands().operand(0).value().IDENTIFIER().getText() == 'true'


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
                "line 3, column 29: parameter takes the number of an input, found '%In0'",
            ),
            (
                ['%In1 = f32[4] parameter(0,1);', 'ROOT %Out0 = f32[4] add(%In0, %In1);'],
                'line 3, column 19: parameter takes 1 operand, found 2',
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
WORDS = ' '.join(FAMILIES.values()).split()

# A value of each form an attribute takes
SAMPLES = {INT: '0', INTS: '{0}', ONE_INT: '{0}', RANGES: '{[0:4]}', BOOL: 'true', NUMBER: '0.5'}


def row_lines(word):
    """Lines that write word with the operands and the required attributes of its row."""
    takes, attributes = OPERATIONS[word]
    # parameter declares an input; any other word computes the output
    if takes == NUMBER_OF_INPUT:
        return ['%In1 = f32[4] parameter(1);', COPY]
    if takes == LITERAL:
        operands = '0'
    else:
        count = takes[0] if isinstance(takes, tuple) else takes
        operands = ', '.join(['%In0'] * count)
    given = ''.join(
        f', {name}={form[0] if isinstance(form, tuple) else SAMPLES[form]}'
        for name, (form, required) in attributes.items()
        if required
    )
    return [f'ROOT %Out0 = f32[4] {word}({operands}){given};']


TYPES = 'pred s2 s4 s8 s16 s32 s64 u2 u4 u8 u16 u32 u64 f8e4m3fn f8e5m2 f16 bf16 f32 f64'.split()


class TestWords:
    def test_lists_match_grammar(self):
        assert sorted(lexed('OPERATION')) == sorted(WORDS)
        assert sorted(lexed('TYPE')) == sorted(TYPES)

    @pytest.mark.parametrize('op', WORDS)
    def test_operation(self, op):
        tree = parse(spec(*row_lines(op)))
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


def rendered(word):
    """The docs' row of an operation word, from its row of the table."""
    takes, attributes = OPERATIONS[word]
    if isinstance(takes, tuple):
        takes = f'{takes[0]} or more'
    given = [
        f'`{name}`: '
        + (form if isinstance(form, str) else 'one of ' + ', '.join(form))
        + ('' if required else ', optional')
        for name, (form, required) in attributes.items()
    ]
    return (f'`{word}`', str(takes), '; '.join(given) or 'none')


class TestDocs:
    def test_operations_table_lists_the_words_by_family(self):
        with open(os.path.join(DOCS, 'operations.md')) as file:
            text = file.read()
        section = text.split('\n## ')[0]
        rows = [row.split('|') for row in section.splitlines() if row.startswith('| ')][2:]
        table = {row[1].strip(): ' '.join(re.findall(r'`(\w+)`', row[2])) for row in rows}
        assert table == FAMILIES

    def test_operation_takes_table_holds_each_row(self):
        with open(os.path.join(DOCS, 'operations.md')) as file:
            text = file.read()
        section = text.split('\n## What an operation takes\n')[1].split('\n## ')[0]
        rows = [row.split('|') for row in section.splitlines() if row.startswith('| ')][2:]
        table = [tuple(cell.strip() for cell in row[1:4]) for row in rows]
        assert table == [rendered(word) for word in OPERATIONS]

    def test_type_sentence_lists_the_types(self):
        with open(os.path.join(DOCS, 'semantics.md')) as file:
            sentence = re.search(r'^A type is one of (.*?), as', file.read(), re.MULTILINE)
        assert sorted(re.findall(r'`(\w+)`', sentence.group(1))) == sorted(TYPES)

    def test_several_outputs_example_loads(self):
        with open(os.path.join(DOCS, 'semantics.md')) as file:
            found = re.search(
                r'^ENTRY \{\n    %In0 = f32\[8\].*?^\}$', file.read(), re.MULTILINE | re.DOTALL
            )
        instr = Accelerator('Readme', base_dir='.').add_instruction('split', [], [])
        instr.set_inputs([['d0', ['0'], ['32']]])
        instr.set_outputs([['d0', ['32'], ['16']], ['d0', ['48'], ['16']]])
        instr.add_semantics(found.group(0))
        assert instr.instr_semantics_ast.instruction(2).ROOT() is not None


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
        tokens = IDLV2Lexer(InputStream(text)).getAllTokens()
        assert [(token.type, token.text) for token in tokens] == [(IDLV2Lexer.IDENTIFIER, text)]

    def test_integer_stays_int(self):
        tree = parse(spec('ROOT %Out0 = s32[1] constant(7);'))
        value = tree.instruction(1).operands().operand(0).value()
        assert value.INT().getText() == '7'
        assert value.NUMBER() is None

    def test_number_attribute(self):
        operands = ', '.join(['%In0'] * 5)
        line = (
            f'ROOT %Out0 = f32[4] batch_norm_inference({operands}), epsilon=-0.5, feature_index=0;'
        )
        tree = parse(spec(line))
        value = tree.instruction(1).attributes().attribute(0).attribute_value().value()
        assert value.NUMBER().getText() == '-0.5'

    def test_signed_brace_list(self):
        line = 'edge_padding_low={-1, 0}, edge_padding_high={2, -0}, interior_padding={0, 0};'
        tree = parse(spec('%z = f32[] constant(0);', f'ROOT %Out0 = f32[4] pad(%In0, %z), {line}'))
        attribute = tree.instruction(2).attributes().attribute(1)
        values = attribute.attribute_value().brace_list().value()
        assert [v.getText() for v in values] == ['2', '-0']
        assert [v.NUMBER() is not None for v in values] == [False, True]


class TestShapes:
    def test_rank0_result(self):
        tree = parse(spec('ROOT %Out0 = f32[] constant(-1);'))
        result = tree.instruction(1).result_type()
        assert result.TYPE().getText() == 'f32'
        assert result.shape() is None

    def test_ranked_result(self):
        tree = parse(spec('ROOT %Out0 = f32[`@c.n`,4] broadcast(%In0), dimensions={1};'))
        shape = tree.instruction(1).result_type().shape()
        assert [dim.getText() for dim in shape.dim()] == ['`@c.n`', '4']
        assert (shape.dim(0).EXPRESSION().getText(), shape.dim(1).INT().getText()) == (
            '`@c.n`',
            '4',
        )

    @pytest.mark.parametrize('dim', ['-1', '0.5', '1e3', 'n', '%In0'])
    def test_dimension_is_an_integer_or_an_expression(self, dim):
        with pytest.raises(SyntaxError, match='t: semantics line 3, column 22'):
            parse(spec(f'ROOT %Out0 = f32[{dim}] copy(%In0);'))


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

    def test_operation_name(self):
        tree = parse(spec('ROOT %Out0 = f32[2] slice(%In0), slice={[0:2]};'))
        attribute = tree.instruction(1).attributes().attribute(0)
        assert attribute.name().getText() == 'slice'
        assert attribute.name().OPERATION() is not None

    def test_slice_list(self):
        tree = parse(spec('ROOT %Out0 = f32[2] slice(%In0), slice={[0:4:2]};'))
        attribute = tree.instruction(1).attributes().attribute(0)
        assert attribute.name().getText() == 'slice'
        assert attribute.attribute_value().slice_list().getText() == '{[0:4:2]}'


class TestOperations:
    def test_one_row_per_word_in_the_grammars_order(self):
        assert list(OPERATIONS) == lexed('OPERATION')

    @pytest.mark.parametrize(
        'lines',
        [
            [
                'ROOT %Out0 = f32[4] dot(%In0, %In0), lhs_contracting_dims={}, rhs_contracting_dims={};'
            ],
            [
                '%Out0 = f32[4] copy(%In0);',
                'ROOT %Out1 = f32[8] concatenate(%In0, %Out0), dimensions={0};',
            ],
            ['ROOT %Out0 = pred[4] compare(%In0, %In0), type=TOTALORDER, direction=LT;'],
            ['ROOT %Out0 = f32[2] slice(%In0), slice={[`@c.n`:4:2]};'],
            ['ROOT %Out0 = s32[] constant(`@c.n`);'],
        ],
        ids=[
            'empty_contracting_lists',
            'several_operands',
            'any_order',
            'expression_bound',
            'expression_constant',
        ],
    )
    def test_line_loads(self, lines):
        tree = parse(spec(*lines))
        assert tree.instruction()[-1].ROOT() is not None

    @pytest.mark.parametrize(
        'lines, message',
        [
            (
                ['ROOT %Out0 = f32[4] add(%In0);'],
                'line 3, column 25: add takes 2 operands, found 1',
            ),
            (
                ['ROOT %Out0 = f32[4] abs(%In0, %In0);'],
                'line 3, column 25: abs takes 1 operand, found 2',
            ),
            (
                ['ROOT %Out0 = f32[4] concatenate(), dimensions={0};'],
                'line 3, column 25: concatenate takes 1 or more operands, found 0',
            ),
            (
                ['ROOT %Out0 = f32[4] add(%In0, 1);'],
                "line 3, column 35: add takes values as operands, found '1'",
            ),
            (
                ['ROOT %Out0 = f32[4] multiply(%In0, -0.5);'],
                "line 3, column 40: multiply takes values as operands, found '-0.5'",
            ),
            (
                ['ROOT %Out0 = f32[] constant(%In0);'],
                "line 3, column 33: constant takes a number, true, false or an expression, found '%In0'",
            ),
            (
                ['ROOT %Out0 = f32[4] add(%In0, %b);'],
                "line 3, column 35: '%b' is defined by no earlier line",
            ),
            (
                [
                    '%a = f32[4] copy(%In0);',
                    '%a = f32[4] negate(%In0);',
                    'ROOT %Out0 = f32[4] add(%a, %a);',
                ],
                "line 4, column 5: '%a' is defined twice",
            ),
            (
                ['ROOT %Out0 = f32[4] add(%In0, %In0), dimensions={0};'],
                "line 3, column 42: add has no attribute 'dimensions': it takes none",
            ),
            (
                ['ROOT %Out0 = f32[4] transpose(%In0), permutation={0};'],
                "line 3, column 42: transpose has no attribute 'permutation': it takes dimensions",
            ),
            (
                ['ROOT %Out0 = f32[4] transpose(%In0), dimensions={0}, dimensions={0};'],
                "line 3, column 58: transpose is given 'dimensions' twice",
            ),
            (
                ['ROOT %Out0 = f32[4] transpose(%In0);'],
                "line 3, column 25: transpose needs the attribute 'dimensions'",
            ),
            (
                ['ROOT %Out0 = f32[4] dot(%In0, %In0), rhs_contracting_dims={0};'],
                "line 3, column 25: dot needs the attribute 'lhs_contracting_dims'",
            ),
        ],
        ids=[
            'too_few_operands',
            'too_many_operands',
            'fewer_than_the_least',
            'integer_operand',
            'number_operand',
            'value_as_constant',
            'undefined_value',
            'value_defined_twice',
            'attribute_of_a_word_with_none',
            'unknown_attribute',
            'attribute_given_twice',
            'missing_attribute',
            'dot_without_its_contracting_lists',
        ],
    )
    def test_line_fails(self, lines, message):
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics {message}')):
            parse(spec(*lines))

    @pytest.mark.parametrize(
        'line, message',
        [
            (
                'iota(), iota_dimension={0}',
                "column 48: 'iota_dimension' of iota takes an integer, found '{0}'",
            ),
            (
                'transpose(%In0), dimensions=0',
                "column 53: 'dimensions' of transpose takes a list of integers, found '0'",
            ),
            (
                'transpose(%In0), dimensions={0.5}',
                "column 53: 'dimensions' of transpose takes a list of integers, found '{0.5}'",
            ),
            (
                'concatenate(%In0), dimensions={0,1}',
                "column 55: 'dimensions' of concatenate takes a list of one integer, found '{0,1}'",
            ),
            (
                'slice(%In0), slice={0,4}',
                "column 44: 'slice' of slice takes a list of ranges, found '{0,4}'",
            ),
            (
                'cholesky(%In0), lower=1',
                "column 47: 'lower' of cholesky takes true or false, found '1'",
            ),
            (
                'compare(%In0, %In0), direction=lt',
                "column 56: 'direction' of compare takes one of EQ, NE, GE, GT, LE, LT, found 'lt'",
            ),
            (
                'batch_norm_inference('
                + ', '.join(['%In0'] * 5)
                + '), epsilon=small, feature_index=0',
                "column 85: 'epsilon' of batch_norm_inference takes a number, found 'small'",
            ),
        ],
        ids=[
            'integer',
            'list',
            'list_of_decimals',
            'list_of_one',
            'ranges',
            'boolean',
            'word',
            'number',
        ],
    )
    def test_malformed_attribute_fails(self, line, message):
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics line 3, {message}')):
            parse(spec(f'ROOT %Out0 = f32[4] {line};'))
