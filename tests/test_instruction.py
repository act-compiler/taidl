"""Tests for the instruction API"""

import re

import pytest
from taidl import Accelerator, State


def make():
    acc = Accelerator('Instr', base_dir='.')
    acc.add_data_model('d1', [64], [16], 's8')
    return acc


def two_inputs():
    instr = make().add_instruction('t', ['n'], ['x', 'y', 'o'])
    instr.set_inputs([['d1', ['@a.x'], ['@c.n']], ['d1', ['@a.y + 1'], ['1']]])
    instr.set_outputs([['d1', ['@a.o'], ['@c.n']]])
    return instr


class TestParameterNames:
    def test_every_parameter_by_keyword(self):
        acc = Accelerator(name='Instr', base_dir='.')
        acc.add_data_model(name='d1', dimensions=[64], unit_dim=[16], var_type='s8')
        acc.add_initial_state(name='busy', value=0)
        instr = acc.add_instruction(name='t', computation_attr=['n'], addressing_attr=['x'])
        assert (instr.instruction, instr.comp_attr, instr.parameters) == ('t', ['n'], ['x'])
        assert [model.var_name for model in acc.data_model] == ['d0', 'd1']
        assert acc.state == [State('busy', 0)]


class TestConstraints:
    def test_add_constraints_appends(self):
        instr = make().add_instruction('t', ['n'], ['x'], constraints=['@c.n <= 4'])
        instr.add_constraints(['@a.x >= 0', '@a.x < 64'])
        instr.add_constraints(['@c.n >= 1'])
        assert instr.constraints == ['@c.n <= 4', '@a.x >= 0', '@a.x < 64', '@c.n >= 1']


class TestStringLists:
    @pytest.mark.parametrize(
        'what', ['computation_attr', 'addressing_attr', 'update', 'constraints']
    )
    def test_add_instruction_refuses_one_string(self, what):
        given = {'computation_attr': [], 'addressing_attr': [], what: 'n'}
        message = f't: {what} takes a list of strings, not one string'
        with pytest.raises(TypeError, match=message):
            make().add_instruction('t', **given)

    def test_add_constraints_refuses_one_string(self):
        instr = make().add_instruction('t', [], ['x'])
        message = 't: add_constraints takes a list of strings, not one string'
        with pytest.raises(TypeError, match=message):
            instr.add_constraints('@a.x >= 0')


class TestFreshLists:
    @pytest.mark.parametrize(
        'field, line', [('update', '@s.busy = 1'), ('constraints', '@a.x >= 0')]
    )
    def test_fresh_list_per_instruction(self, field, line):
        acc = make()
        acc.add_initial_state('busy', 0)
        given = [line]
        getattr(acc.add_instruction('a', [], ['x'], **{field: given}), field).append(line)
        getattr(acc.add_instruction('b', [], ['x']), field).append(line)
        assert given == [line]
        assert getattr(acc.add_instruction('c', [], ['x']), field) == []

    def test_attribute_lists_copied(self):
        comp, addr = ['n'], ['x']
        instr = make().add_instruction('t', comp, addr)
        comp.append('m')
        addr.append('y')
        assert (instr.comp_attr, instr.parameters) == (['n'], ['x'])

    def test_region_and_flag_lists_copied(self):
        instr = make().add_instruction('t', [], ['x', 'o'])
        inputs, outputs, flags = [['d1', ['@a.x'], ['1']]], [['d1', ['@a.o'], ['1']]], [True]
        instr.set_inputs(inputs)
        instr.set_outputs(outputs)
        instr.set_inplace(flags)
        for given in (inputs, outputs, flags):
            given.clear()
        assert instr.instr_inputs == [['d1', ['@a.x'], ['1']]]
        assert instr.instr_outputs == [['d1', ['@a.o'], ['1']]]
        assert instr.inplace == [True]


class TestBuffers:
    def test_find_data_model(self):
        instr = make().add_instruction('t', [], ['x'])
        assert instr.find_data_model('d1').var_name == 'd1'

    def test_undeclared_buffer_fails(self):
        instr = make().add_instruction('t', [], ['x'])
        with pytest.raises(ValueError, match="t: no data model is named 'd9'"):
            instr.find_data_model('d9')


class TestInplace:
    def test_unmarked_by_default(self):
        assert two_inputs().inplace == [False, False]

    def test_set_inplace(self):
        instr = two_inputs()
        instr.set_inplace([False, True])
        assert instr.inplace == [False, True]

    def test_set_inputs_resets(self):
        instr = two_inputs()
        instr.set_inplace([True, True])
        instr.set_inputs([['d1', ['@a.x'], ['@c.n']]])
        assert instr.inplace == [False]

    @pytest.mark.parametrize('flags', [[True], [True, False, False]], ids=['short', 'long'])
    def test_one_flag_per_input(self, flags):
        with pytest.raises(ValueError, match='t: set_inplace needs one flag per input'):
            two_inputs().set_inplace(flags)

    def test_before_inputs_fails(self):
        with pytest.raises(ValueError, match='t: set_inplace needs one flag per input'):
            make().add_instruction('t', [], ['x']).set_inplace([True])


class KeepOff:
    """The checks every non-overlap mark shares."""

    def mark(self, instr, flags):
        getattr(instr, self.method)(flags)

    @pytest.mark.parametrize('found', [0, 2])
    def test_needs_one_output(self, found):
        instr = make().add_instruction('t', [], ['x', 'o'])
        instr.set_inputs([['d1', ['@a.x'], ['1']]])
        instr.set_outputs([['d1', ['@a.o'], ['1']]] * found)
        message = f't: {self.method} needs exactly one output, found {found}'
        with pytest.raises(ValueError, match=message):
            self.mark(instr, [True])

    def test_one_flag_per_input(self):
        with pytest.raises(ValueError, match=f't: {self.method} needs one flag per input'):
            self.mark(two_inputs(), [True])

    def test_not_also_inplace(self):
        instr = two_inputs()
        instr.set_inplace([False, True])
        with pytest.raises(ValueError, match=f't: {self.method} marks an input also in place'):
            self.mark(instr, [False, True])

    def test_same_buffer(self):
        instr = make().add_instruction('t', [], ['x', 'o'])
        instr.set_inputs([['d0', ['@a.x'], ['1']]])
        instr.set_outputs([['d1', ['@a.o'], ['1']]])
        with pytest.raises(ValueError, match=f't: {self.method} marks an input outside d1'):
            self.mark(instr, [True])


class TestApart(KeepOff):
    method = 'set_apart'

    def test_constraint(self):
        instr = two_inputs()
        instr.set_apart([False, True])
        assert instr.constraints == ['@a.o + @c.n <= (@a.y + 1) or (@a.y + 1) + 1 <= @a.o']

    def test_any_addressed_dimension(self):
        acc = make()
        acc.add_data_model('d2', [8, 8], [16], 's8')
        instr = acc.add_instruction('t', [], ['q', 'r', 'x', 'o'], constraints=['@a.q >= 0'])
        instr.set_inputs([['d2', ['@a.r', '@a.x'], ['2', '4']]])
        instr.set_outputs([['d2', ['@a.q', '@a.o'], ['2', '4']]])
        instr.set_apart([True])
        apart = '@a.q + 2 <= @a.r or @a.r + 2 <= @a.q or @a.o + 4 <= @a.x or @a.x + 4 <= @a.o'
        assert instr.constraints == ['@a.q >= 0', apart]

    def test_only_where_starts_differ(self):
        acc = make()
        acc.add_data_model('d2', [8, 8], [16], 's8')
        instr = acc.add_instruction('t', ['n'], ['r', 'x', 'o'])
        instr.set_inputs([['d2', ['@a.r', '@a.x'], ['@c.n', '4']]])
        instr.set_outputs([['d2', ['@a.r', '@a.o'], ['1', '4']]])
        instr.set_apart([True])
        assert instr.constraints == ['@a.o + 4 <= @a.x or @a.x + 4 <= @a.o']

    def test_same_starts_refused(self):
        instr = make().add_instruction('t', ['n'], ['x'])
        instr.set_inputs([['d1', ['@a.x'], ['@c.n']]])
        instr.set_outputs([['d1', ['@a.x'], ['1']]])
        with pytest.raises(ValueError, match="t: set_apart marks an input at the output's own"):
            instr.set_apart([True])


class TestNoPartialOverlap(KeepOff):
    method = 'set_no_partial_overlap'

    def test_same_start_or_apart(self):
        instr = two_inputs()
        instr.set_no_partial_overlap([True, False])
        assert instr.constraints == ['@a.o == @a.x or @a.o + @c.n <= @a.x or @a.x + @c.n <= @a.o']

    def test_only_where_starts_differ(self):
        acc = make()
        acc.add_data_model('d2', [8, 8], [16], 's8')
        instr = acc.add_instruction('t', ['n'], ['r', 'x', 'o'])
        instr.set_inputs([['d2', ['@a.r', '@a.x'], ['@c.n', '4']]])
        instr.set_outputs([['d2', ['@a.r', '@a.o'], ['1', '4']]])
        instr.set_no_partial_overlap([True])
        assert instr.constraints == ['@a.o == @a.x or @a.o + 4 <= @a.x or @a.x + 4 <= @a.o']

    def test_same_starts_add_nothing(self):
        instr = make().add_instruction('t', ['n'], ['x'])
        instr.set_inputs([['d1', ['@a.x'], ['@c.n']]])
        instr.set_outputs([['d1', ['@a.x'], ['1']]])
        instr.set_no_partial_overlap([True])
        assert instr.constraints == []


class TestInitialState:
    def test_in_order(self):
        acc = make()
        acc.add_initial_state('preload', 0)
        acc.add_initial_state('fifo_occupancy', 2)
        assert acc.state == [State('preload', 0), State('fifo_occupancy', 2)]
        assert [(state.name, state.value) for state in acc.state] == [
            ('preload', 0),
            ('fifo_occupancy', 2),
        ]

    def test_update_kept(self):
        acc = make()
        acc.add_initial_state('busy', 0)
        instr = acc.add_instruction('t', [], ['x'], update=['@s.busy = 1'])
        assert (acc.state, instr.update) == ([State('busy', 0)], ['@s.busy = 1'])


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
