"""Instruction set definitions for TAIDLv2"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from antlr4 import CommonTokenStream, InputStream

from .data_model import DataModel
from .antlr4 import IDLV2Lexer, IDLV2Parser


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

    def find_data_model(self, name: str) -> DataModel:
        for model in self.data_models:
            if model.var_name == name:
                break
        else:
            model = None
        assert model != None, f"Data buffer '{name}' not found"
        return model

    def set_inputs(self, inputs: List[Tuple[str, List[str], List[str]]]):
        self.instr_inputs = inputs

    def set_outputs(self, outputs: List[Tuple[str, List[str], List[str]]]):
        self.instr_outputs = outputs

    def add_semantics(self, semantics: str):
        self.instr_semantics_str = semantics
        self.instr_semantics_ast = None
        if semantics and semantics.strip():
            self.instr_semantics_ast = self.parse_semantics(semantics)

    def parse_semantics(self, semantics: str):
        """Parse semantics into AST eagerly to catch syntax errors early"""
        input_stream = InputStream(semantics)
        lexer = IDLV2Lexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = IDLV2Parser(stream)
        tree = parser.module()
        if parser.getNumberOfSyntaxErrors() > 0:
            raise SyntaxError(f"Failed to parse semantics for instruction '{self.instruction}'")
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
        return tree

    def add_constraints(self, constraints: str):
        lines = constraints.strip().split('\n')
        self.constraints = [line for line in lines if line.strip()]
