import re

import pytest

from taidl import Accelerator
from taidl.antlr4 import IDLV2ExprParser

EXPECTING = "expecting {ADDRESSING, COMPUTATIONAL, STATE, '-', '(', INT}"


def make():
    acc = Accelerator('Expr', base_dir='.')
    acc.add_data_model('d1', [64], [16], 's8')
    acc.add_initial_state('mode', 0)
    return acc


def instruction():
    return make().add_instruction('t', ['n', 'm'], ['x', 'y'])


class TestValues:
    @pytest.mark.parametrize(
        'text',
        [
            '128',
            '@c.n',
            '@a.x * 8 + 4',
            '@s.mode',
            '(@c.n + @c.m) * 2',
            '@c.n / 16 / @c.m',
            '@c.n % 4',
            '-@c.n',
            '4 - -1',
            '@c.n *\n 2',
        ],
    )
    def test_size_parses(self, text):
        instr = instruction()
        instr.set_inputs([['d1', ['@a.x'], [text]]])
        tree = instr.instr_input_asts[0][2][0]
        assert isinstance(tree, IDLV2ExprParser.ExpressionContext)
        assert tree.getText() == ''.join(text.split())

    @pytest.mark.parametrize(
        'text, message',
        [
            ('0.5', "line 1, column 2: mismatched input '.' expecting <EOF>"),
            ('007', "line 1, column 2: mismatched input '0' expecting <EOF>"),
            ('n * 2', f"line 1, column 1: mismatched input 'n' {EXPECTING}"),
            ('@l.i', f"line 1, column 1: mismatched input '@' {EXPECTING}"),
            ('', f"line 1, column 1: mismatched input '<EOF>' {EXPECTING}"),
            ('+@c.n', f"line 1, column 1: extraneous input '+' {EXPECTING}"),
            ('2 ** @c.n', f"line 1, column 4: extraneous input '*' {EXPECTING}"),
            ('@c.n // 2', f"line 1, column 7: extraneous input '/' {EXPECTING}"),
            ('@c.n << 2', "line 1, column 6: mismatched input '<' expecting <EOF>"),
            ('min(@c.n, @c.m)', f"line 1, column 1: extraneous input 'min' {EXPECTING}"),
            ('1 if @c.n == 1 else 2', "line 1, column 3: mismatched input 'if' expecting <EOF>"),
            ('@c.n == 1', "line 1, column 6: mismatched input '==' expecting <EOF>"),
            ('@c.n +', f"line 1, column 7: mismatched input '<EOF>' {EXPECTING}"),
        ],
        ids=[
            'decimal',
            'leading_zero',
            'bare_word',
            'unknown_reference',
            'empty',
            'unary_plus',
            'power',
            'floor_division',
            'shift',
            'function',
            'conditional',
            'condition',
            'unfinished',
        ],
    )
    def test_size_fails(self, text, message):
        with pytest.raises(SyntaxError, match=re.escape(f"t: size '{text}' {message}")):
            instruction().set_inputs([['d1', ['@a.x'], [text]]])

    @pytest.mark.parametrize('setter', ['set_inputs', 'set_outputs'])
    def test_start_fails(self, setter):
        message = f"t: start '@a.x +' line 1, column 7: mismatched input '<EOF>' {EXPECTING}"
        with pytest.raises(SyntaxError, match=re.escape(message)):
            getattr(instruction(), setter)([['d1', ['@a.x +'], ['1']]])

    def test_regions_held_parsed(self):
        instr = instruction()
        instr.set_inputs([['d0', [0], ['@c.n * 128']]])
        instr.set_outputs([['d1', ['@a.x * 2 + 1'], [4]]])
        held = [
            [buffer, [tree.getText() for tree in starts], [tree.getText() for tree in sizes]]
            for buffer, starts, sizes in instr.instr_input_asts + instr.instr_output_asts
        ]
        assert held == [['d0', ['0'], ['@c.n*128']], ['d1', ['@a.x*2+1'], ['4']]]


SEMANTICS = """ENTRY {
    %In0 = f32[`@c.n * 2`,4] parameter(0);
    %a = f32[`@c.n *
 2`,4] reshape(%In0);
    ROOT %Out0 = f32[2,2] slice(%a), slice={[0:2], [0:`@c.m`:2]};
}
"""


class TestSemantics:
    def test_each_expression_held_by_its_node(self):
        instr = instruction()
        instr.add_semantics(SEMANTICS)
        lines = instr.instr_semantics_ast.instruction()
        nodes = [
            lines[0].result_type().shape().dim(0).EXPRESSION(),
            lines[1].result_type().shape().dim(0).EXPRESSION(),
        ]
        nodes.append(
            lines[2].attributes().attribute(0).attribute_value().slice_list().value(3).EXPRESSION()
        )
        trees = [instr.instr_expression_asts[node] for node in nodes]
        assert [tree.getText() for tree in trees] == ['@c.n*2', '@c.n*2', '@c.m']
        assert len(instr.instr_expression_asts) == 3

    @pytest.mark.parametrize(
        'shape, message',
        [
            ('`@c.n *`,4', f"line 3, column 29: mismatched input '<EOF>' {EXPECTING}"),
            ('`4 +\n @c.n ** 2`', f"line 4, column 8: extraneous input '*' {EXPECTING}"),
        ],
        ids=['first_line', 'second_line'],
    )
    def test_expression_fails_at_its_line_and_column(self, shape, message):
        text = f'ENTRY {{\n    %In0 = f32[4] parameter(0);\n    ROOT %Out0 = f32[{shape}] copy(%In0);\n}}\n'
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics {message}')):
            instruction().add_semantics(text)
