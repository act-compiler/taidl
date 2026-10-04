"""Instruction set definitions for TAIDLv2"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

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
    cost: str
    update: List[str]

    instr_inputs: List[Tuple[str, List[str], List[str]]]
    instr_outputs: List[Tuple[str, List[str], List[str]]]
    instr_semantics_str: str
    instr_semantics_ast: Optional[IDLV2Parser.ModuleContext]
    inputs_given: bool
    outputs_given: bool

    def __init__(
        self,
        instruction: str,
        comp_attr: List[str],
        addr_attr: List[str],
        constraints: List[str],
        cost: str,
        update: List[str],
        data_models: List[DataModel],
    ):
        self.instruction = instruction.replace(' ', '_')
        self.comp_attr = comp_attr
        self.parameters = addr_attr
        self.constraints = constraints
        self.cost = cost
        self.update = update
        self.data_models = data_models
        self.instr_inputs = []
        self.instr_outputs = []
        self.instr_semantics_str = ''
        self.instr_semantics_ast = None
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
        self.instr_inputs = inputs
        self.inputs_given = True

    def set_outputs(self, outputs: List[Tuple[str, List[str], List[str]]]):
        if self.instr_semantics_ast is not None:
            self.check_values(self.instr_semantics_ast, 'output', outputs)
        self.instr_outputs = outputs
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

    def add_constraints(self, constraints: str):
        lines = constraints.strip().split('\n')
        self.constraints = self.constraints + [line for line in lines if line.strip()]
