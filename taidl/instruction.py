"""Instruction set definitions for TAIDLv2"""

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .data_model import DataModel
from .antlr4 import IDLV2Lexer, IDLV2Parser


class SyntaxErrors(ErrorListener):
    """Collect each syntax error with its line and column, both from 1."""

    def __init__(self):
        self.found = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.found.append(f'line {line}, column {column + 1}: {msg}')


@dataclass
class Instruction:
    instruction: str
    comp_attr: List[str]
    parameters: List[str]
    constraints: List[str]
    data_models: List[DataModel]
    update: List[str]

    instr_inputs: List[Tuple[str, List[str], List[str]]]
    instr_outputs: List[Tuple[str, List[str], List[str]]]
    instr_semantics_str: str
    instr_semantics_ast: Optional[IDLV2Parser.ModuleContext]
    inplace: List[bool]
    inputs_given: bool
    outputs_given: bool

    def __init__(
        self,
        name: str,
        comp_attr: List[str],
        addr_attr: List[str],
        constraints: Sequence[str],
        update: Sequence[str],
        data_models: List[DataModel],
    ):
        self.instruction = name.replace(' ', '_')
        self.comp_attr = strings(name, 'computation_attr', comp_attr)
        self.parameters = strings(name, 'addressing_attr', addr_attr)
        self.constraints = strings(name, 'constraints', constraints)
        self.update = strings(name, 'update', update)
        self.data_models = data_models
        self.instr_inputs = []
        self.instr_outputs = []
        self.instr_semantics_str = ''
        self.instr_semantics_ast = None
        self.inplace = []
        # Which of set_inputs and set_outputs has run
        self.inputs_given = False
        self.outputs_given = False

    def find_data_model(self, name: str) -> DataModel:
        for model in self.data_models:
            if model.var_name == name:
                break
        else:
            model = None
        assert model != None, f"Data buffer '{name}' not found"
        return model

    def set_inputs(self, inputs: List[Tuple[str, List[str], List[str]]]):
        if self.instr_semantics_ast is not None:
            self.check_values(self.instr_semantics_ast, 'input', inputs)
        self.instr_inputs = list(inputs)
        self.inplace = [False] * len(inputs)
        self.inputs_given = True

    def set_outputs(self, outputs: List[Tuple[str, List[str], List[str]]]):
        if self.instr_semantics_ast is not None:
            self.check_values(self.instr_semantics_ast, 'output', outputs)
        self.instr_outputs = list(outputs)
        self.outputs_given = True

    def check_values(
        self,
        semantics: IDLV2Parser.ModuleContext,
        kind: str,
        regions: List[Tuple[str, List[str], List[str]]],
    ):
        """Refuse an input or output region without its value, or a value without its region."""
        # Input region k has %In<k>, output region k %Out<k>
        prefix = '%In' if kind == 'input' else '%Out'
        expected = [f'{prefix}{k}' for k in range(len(regions))]
        values = [line.IDENTIFIER().getSymbol() for line in semantics.instruction()]
        values = [value for value in values if re.fullmatch(rf'{prefix}\d+', value.text)]
        for k, name in enumerate(expected):
            if name not in [value.text for value in values]:
                raise SyntaxError(
                    f"{self.instruction}: semantics has no '{name}' for {kind} region {k}"
                )
        for value in values:
            if value.text not in expected:
                raise SyntaxError(
                    f'{self.instruction}: semantics line {value.line}, column {value.column + 1}: '
                    f"'{value.text}' has no {kind} region, set_{kind}s gave {len(regions)}"
                )

    def set_inplace(self, inplace: List[bool]):
        """Mark the inputs this instruction overwrites, one flag per input; set_inputs resets them."""
        if len(inplace) != len(self.instr_inputs):
            raise ValueError(f'{self.instruction}: set_inplace needs one flag per input')
        self.inplace = list(inplace)

    def set_apart(self, apart: List[bool]):
        """Mark the inputs the output never overlaps, one flag per input.

        Each marked input adds one constraint: the output lies apart from it along
        at least one addressed dimension whose starts are spelled differently.
        """
        self.keep_off('set_apart', apart, whole=False)

    def set_no_partial_overlap(self, no_partial: List[bool]):
        """Mark the inputs the output shares its starts with or lies apart from, one flag per input.

        Each marked input adds one constraint per addressed dimension whose starts are
        spelled differently: the starts there are equal, or the output lies apart from it.
        """
        self.keep_off('set_no_partial_overlap', no_partial, whole=True)

    def keep_off(self, method: str, flags: List[bool], whole: bool):
        """Keep the output apart from each flagged input, or sharing its starts if `whole`."""
        name = self.instruction
        if len(self.instr_outputs) != 1:
            found = len(self.instr_outputs)
            raise ValueError(f'{name}: {method} needs exactly one output, found {found}')
        if len(flags) != len(self.instr_inputs):
            raise ValueError(f'{name}: {method} needs one flag per input')
        out_buffer, out_starts, out_sizes = self.instr_outputs[0]
        for flag, inplace, (buffer, starts, sizes) in zip(flags, self.inplace, self.instr_inputs):
            if not flag:
                continue
            if inplace:
                raise ValueError(f'{name}: {method} marks an input also in place')
            if buffer != out_buffer:
                raise ValueError(f'{name}: {method} marks an input outside {out_buffer}')
            # Per dim, unlike starts: one ends before the other
            equals, sides = [], []
            for out_start, out_size, start, size in zip(out_starts, out_sizes, starts, sizes):
                if str(out_start).strip() == str(start).strip():
                    continue
                equals.append(f'{term(out_start)} == {term(start)}')
                sides.append(f'{term(out_start)} + {term(out_size)} <= {term(start)}')
                sides.append(f'{term(start)} + {term(size)} <= {term(out_start)}')
            apart = ' or '.join(sides)
            if whole:
                # Or wholly over it: equal starts in each such dim
                self.constraints = self.constraints + [f'{equal} or {apart}' for equal in equals]
            elif sides:
                self.constraints = self.constraints + [apart]
            else:
                raise ValueError(f"{name}: {method} marks an input at the output's own starts")

    def add_semantics(self, semantics: str):
        self.instr_semantics_str = semantics
        tree = self.parse_semantics(semantics)
        # Against the regions given so far, even none
        if self.inputs_given:
            self.check_values(tree, 'input', self.instr_inputs)
        if self.outputs_given:
            self.check_values(tree, 'output', self.instr_outputs)
        self.instr_semantics_ast = tree

    def parse_semantics(self, semantics: str):
        """Parse semantics into AST eagerly to catch syntax errors early"""
        input_stream = InputStream(semantics)
        lexer = IDLV2Lexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = IDLV2Parser(stream)
        # Collect syntax errors rather than print them
        errors = SyntaxErrors()
        for recognizer in (lexer, parser):
            recognizer.removeErrorListeners()
            recognizer.addErrorListener(errors)
        tree = parser.module()
        if errors.found:
            raise SyntaxError(f'{self.instruction}: semantics {errors.found[0]}')
        # A line names its value with a leading %
        for line in tree.instruction():
            name = line.IDENTIFIER().getSymbol()
            if not name.text.startswith('%'):
                raise SyntaxError(
                    f'{self.instruction}: semantics line {name.line}, column {name.column + 1}: '
                    f"value name '{name.text}' has no leading '%'"
                )
        # One line carries ROOT
        roots = sum(line.ROOT() is not None for line in tree.instruction())
        if roots != 1:
            raise SyntaxError(
                f'{self.instruction}: semantics needs exactly one ROOT, found {roots}'
            )
        # Input k enters as %In<k>, declared by parameter(k) alone
        for line in tree.instruction():
            name = line.IDENTIFIER().getSymbol()
            operation = line.OPERATION().getText()
            if operation == 'parameter':
                # One integer operand, the input's number
                text = line.operands().getText() if line.operands() else ''
                if not re.fullmatch(r'\d+', text):
                    word = line.OPERATION().getSymbol()
                    raise SyntaxError(
                        f'{self.instruction}: semantics line {word.line}, column {word.column + 1}: '
                        f"parameter({text}) needs one integer, the input's number"
                    )
                number = int(text)
                if name.text != f'%In{number}':
                    raise SyntaxError(
                        f'{self.instruction}: semantics line {name.line}, column {name.column + 1}: '
                        f"parameter({text}) declares '%In{number}', not '{name.text}'"
                    )
            elif re.fullmatch(r'%In\d+', name.text):
                raise SyntaxError(
                    f'{self.instruction}: semantics line {name.line}, column {name.column + 1}: '
                    f"'{name.text}' is declared by parameter({name.text[3:]}), not by {operation}"
                )
        # ROOT is on the last output, the highest %Out<k>
        outputs = [line.IDENTIFIER().getText() for line in tree.instruction()]
        outputs = [name for name in outputs if re.fullmatch(r'%Out\d+', name)]
        last = max(outputs, key=lambda name: int(name[4:]), default='%Out0')
        root = next(line for line in tree.instruction() if line.ROOT())
        mark = root.ROOT().getSymbol()
        if root.IDENTIFIER().getText() != last:
            raise SyntaxError(
                f'{self.instruction}: semantics line {mark.line}, column {mark.column + 1}: '
                f"ROOT is on '{root.IDENTIFIER().getText()}', not on the last output '{last}'"
            )
        return tree

    def add_constraints(self, constraints: Sequence[str]):
        """Append constraints to those the instruction already has."""
        self.constraints = self.constraints + strings(
            self.instruction, 'add_constraints', constraints
        )


def strings(instruction: str, what: str, given: Sequence[str]) -> List[str]:
    """A copy of a list of strings; one bare string is refused."""
    if isinstance(given, str):
        raise TypeError(f'{instruction}: {what} takes a list of strings, not one string')
    return list(given)


def term(expr) -> str:
    """One start or size as a constraint term, bracketed unless a single token."""
    text = str(expr).strip()
    return text if re.fullmatch(r'@?[\w.]+', text) else f'({text})'
