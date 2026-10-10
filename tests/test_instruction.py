"""Tests for the instruction API"""

import re

import pytest
from taidl import Accelerator


def make():
    acc = Accelerator('Instr', base_dir='.')
    acc.add_data_model('d1', [64], [16], 's8')
    return acc


def two_inputs():
    instr = make().add_instruction('t', ['n'], ['x', 'y', 'o'])
    instr.set_inputs([['d1', ['@a.x'], ['@c.n']], ['d1', ['@a.y + 1'], ['1']]])
    instr.set_outputs([['d1', ['@a.o'], ['@c.n']]])
    return instr


# t's semantics over the given parameters, %Out0 copying %In0
def semantics(*parameters):
    lines = [f'%In{k} = s8[1,16] parameter({k});' for k in parameters]
    return (
        'ENTRY {\n'
        + ''.join(f'    {line}\n' for line in lines)
        + '    ROOT %Out0 = s8[1,16] copy(%In0);\n}\n'
    )


class TestValues:
    @pytest.mark.parametrize('first', ['regions', 'semantics'])
    def test_each_region_has_its_value(self, first):
        instr = make().add_instruction('t', [], ['x', 'y', 'o'])
        if first == 'semantics':
            instr.add_semantics(semantics(0, 1))
        instr.set_inputs([['d1', ['@a.x'], ['1']], ['d1', ['@a.y'], ['1']]])
        instr.set_outputs([['d1', ['@a.o'], ['1']]])
        if first == 'regions':
            instr.add_semantics(semantics(0, 1))
        assert len(instr.instr_inputs) == 2

    def test_input_region_without_its_value_fails(self):
        with pytest.raises(SyntaxError, match="t: semantics has no '%In1' for input region 1"):
            two_inputs().add_semantics(semantics(0))

    def test_output_region_without_its_value_fails(self):
        instr = two_inputs()
        instr.set_outputs([['d1', ['@a.o'], ['1']], ['d1', ['@a.x'], ['1']]])
        with pytest.raises(SyntaxError, match="t: semantics has no '%Out1' for output region 1"):
            instr.add_semantics(semantics(0, 1))

    def test_value_without_its_region_fails(self):
        instr = make().add_instruction('t', [], ['x'])
        instr.add_semantics(semantics(0, 1))
        message = "t: semantics line 3, column 5: '%In1' has no input region, set_inputs gave 1"
        with pytest.raises(SyntaxError, match=re.escape(message)):
            instr.set_inputs([['d1', ['@a.x'], ['1']]])

    def test_output_value_without_its_region_fails(self):
        instr = make().add_instruction('t', [], ['x'])
        instr.add_semantics(
            'ENTRY {\n'
            '    %In0 = s8[1,16] parameter(0);\n'
            '    %Out0 = s8[1,16] copy(%In0);\n'
            '    ROOT %Out1 = s8[1,16] negate(%In0);\n'
            '}\n'
        )
        message = "t: semantics line 4, column 10: '%Out1' has no output region, set_outputs gave 1"
        with pytest.raises(SyntaxError, match=re.escape(message)):
            instr.set_outputs([['d1', ['@a.x'], ['1']]])

    @pytest.mark.parametrize(
        'kind, message',
        [
            ('inputs', "line 2, column 5: '%In0' has no input region, set_inputs gave 0"),
            ('outputs', "line 3, column 10: '%Out0' has no output region, set_outputs gave 0"),
        ],
    )
    def test_value_after_no_regions_fails(self, kind, message):
        # Refused as when the semantics comes first
        instr = make().add_instruction('t', [], [])
        getattr(instr, f'set_{kind}')([])
        with pytest.raises(SyntaxError, match=re.escape(f't: semantics {message}')):
            instr.add_semantics(semantics(0))
