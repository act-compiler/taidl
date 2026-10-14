"""Instruction set definitions for TAIDLv2"""

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener
from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNode
from antlr4.tree.Trees import Trees

from .data_model import DataModel, State
from .antlr4 import IDLV2ExprLexer, IDLV2ExprParser, IDLV2Lexer, IDLV2Parser
from .operations import check_operations

# Start or size: integer, or expression over attributes and state
Extent = int | str
# A buffer's name, then its starts, then its sizes
Region = Sequence[str | Sequence[Extent]]
# A region parsed: buffer name, start trees, size trees
RegionTrees = list[str | list[IDLV2ExprParser.ExpressionContext]]


class SyntaxErrors(ErrorListener):
    """Collect each syntax error with its line and column, both from 1."""

    def __init__(self):
        self.found = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.found.append((line, column + 1, msg))


@dataclass
class Instruction:
    instruction: str
    comp_attr: List[str]
    parameters: List[str]
    constraints: List[str]
    data_models: List[DataModel]
    state: list[State]
    update: List[str]

    instr_inputs: List[Tuple[str, List[str], List[str]]]
    instr_outputs: List[Tuple[str, List[str], List[str]]]
    instr_semantics_str: str
    instr_semantics_ast: Optional[IDLV2Parser.ModuleContext]
    # Each text above parsed, beside it
    constraint_asts: list[IDLV2ExprParser.ConditionContext]
    update_asts: list[IDLV2ExprParser.UpdateContext]
    instr_input_asts: list[RegionTrees]
    instr_output_asts: list[RegionTrees]
    instr_expression_asts: dict[TerminalNode, IDLV2ExprParser.ExpressionContext]
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
        state: list[State],
    ):
        self.instruction = name.replace(' ', '_')
        self.comp_attr = strings(name, 'computation_attr', comp_attr)
        self.parameters = strings(name, 'addressing_attr', addr_attr)
        # The accelerator's state, complete before any instruction
        self.state = state
        self.constraints, self.constraint_asts = [], []
        self.append_constraints(strings(name, 'constraints', constraints))
        given = strings(name, 'update', update)
        self.update, self.update_asts = given, [self.parse_text('update', text) for text in given]
        self.data_models = data_models
        self.instr_inputs, self.instr_input_asts = [], []
        self.instr_outputs, self.instr_output_asts = [], []
        self.instr_semantics_str = ''
        self.instr_semantics_ast, self.instr_expression_asts = None, {}
        self.inplace = []
        # Which of set_inputs and set_outputs has run
        self.inputs_given = False
        self.outputs_given = False

    def find_data_model(self, name: str) -> DataModel:
        for model in self.data_models:
            if model.var_name == name:
                return model
        raise ValueError(f"{self.instruction}: no data model is named '{name}'")

    def set_inputs(self, inputs: List[Tuple[str, List[str], List[str]]]):
        self.check_regions(inputs)
        trees = self.parse_regions(inputs)
        if self.instr_semantics_ast is not None:
            self.check_values(self.instr_semantics_ast, 'input', inputs)
        self.instr_inputs, self.instr_input_asts = list(inputs), trees
        self.inplace = [False] * len(inputs)
        self.inputs_given = True

    def set_outputs(self, outputs: List[Tuple[str, List[str], List[str]]]):
        self.check_regions(outputs)
        trees = self.parse_regions(outputs)
        if self.instr_semantics_ast is not None:
            self.check_values(self.instr_semantics_ast, 'output', outputs)
        self.instr_outputs, self.instr_output_asts = list(outputs), trees
        self.outputs_given = True

    def check_regions(self, regions: Sequence[Region]):
        """Refuse a buffer the accelerator does not declare."""
        for buffer, _, _ in regions:
            self.find_data_model(buffer)

    def parse_regions(self, regions: Sequence[Region]) -> list[RegionTrees]:
        """Parse each start and size of each region, an integer by its decimal text."""
        return [
            [
                buffer,
                [self.parse_text('start', str(start)) for start in starts],
                [self.parse_text('size', str(size)) for size in sizes],
            ]
            for buffer, starts, sizes in regions
        ]

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
                self.append_constraints([f'{equal} or {apart}' for equal in equals])
            elif sides:
                self.append_constraints([apart])
            else:
                raise ValueError(f"{name}: {method} marks an input at the output's own starts")

    def add_semantics(self, semantics: str):
        self.instr_semantics_str = semantics
        tree = self.parse_semantics(semantics)
        # Each backtick expression, by its node in the tree
        expressions = {
            node: self.parse_text('semantics', node.getText()[1:-1], node.getSymbol())
            for node in Trees.findAllTokenNodes(tree, IDLV2Parser.EXPRESSION)
        }
        # Against the regions given so far, even none
        if self.inputs_given:
            self.check_values(tree, 'input', self.instr_inputs)
        if self.outputs_given:
            self.check_values(tree, 'output', self.instr_outputs)
        self.instr_semantics_ast, self.instr_expression_asts = tree, expressions

    def parse_semantics(self, semantics: str):
        """Parse semantics into AST eagerly to catch syntax errors early"""
        tree, errors = parse(IDLV2Lexer, IDLV2Parser, 'module', semantics)
        if errors:
            line, column, message = errors[0]
            raise SyntaxError(
                f'{self.instruction}: semantics line {line}, column {column}: {message}'
            )
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
        # Each line takes what its word's row gives
        fault = check_operations(tree)
        if fault:
            token, message = fault
            raise SyntaxError(
                f'{self.instruction}: semantics line {token.line}, column {token.column + 1}: '
                f'{message}'
            )
        # Input k enters as %In<k>, declared by parameter(k) alone
        for line in tree.instruction():
            name = line.IDENTIFIER().getSymbol()
            operation = line.OPERATION().getText()
            if operation == 'parameter':
                # Its one integer operand, the input's number
                text = line.operands().getText()
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
        self.append_constraints(strings(self.instruction, 'add_constraints', constraints))

    def append_constraints(self, constraints: list[str]):
        """Parse each constraint and append it, with its tree."""
        trees = [self.parse_text('constraint', text) for text in constraints]
        self.constraints = self.constraints + constraints
        self.constraint_asts = self.constraint_asts + trees

    def parse_text(self, place: str, text: str, token: CommonToken | None = None):
        """Parse a text by its place's entry rule; a fault names the place, its line and column.

        A backtick expression's place is the semantics, and its token says where it stands there.
        """
        tree, errors = parse(IDLV2ExprLexer, IDLV2ExprParser, RULES[place], text)
        if errors:
            raise self.text_error(place, text, token, *errors[0])
        # Each reference, an update's target too, names what is declared
        declared = {
            '@a.': self.parameters,
            '@c.': self.comp_attr,
            '@s.': [variable.name for variable in self.state],
        }
        names = [
            node.getSymbol()
            for reference in (
                IDLV2ExprParser.ADDRESSING,
                IDLV2ExprParser.COMPUTATIONAL,
                IDLV2ExprParser.STATE,
            )
            for node in Trees.findAllTokenNodes(tree, reference)
        ]
        for name in sorted(names, key=lambda symbol: symbol.tokenIndex):
            kind = name.text[:3]
            if name.text[3:] not in declared[kind]:
                message = f"'{name.text}' names no {KINDS[kind]}"
                raise self.text_error(place, text, token, name.line, name.column + 1, message)
        return tree.getChild(0)

    def text_error(
        self,
        place: str,
        text: str,
        token: CommonToken | None,
        line: int,
        column: int,
        message: str,
    ) -> SyntaxError:
        """A fault at a line and column of a text, both from 1."""
        if token is None:
            where = f"{place} '{text}' line {line}, column {column}"
            return SyntaxError(f'{self.instruction}: {where}: {message}')
        # Counted in the semantics, past the opening backtick
        if line == 1:
            column += token.column + 1
        line += token.line - 1
        return SyntaxError(f'{self.instruction}: semantics line {line}, column {column}: {message}')


# Each place's entry rule in the expression grammar
RULES = {
    'start': 'expression_text',
    'size': 'expression_text',
    'semantics': 'expression_text',
    'constraint': 'constraint_text',
    'update': 'update_text',
}


# What each kind of reference names
KINDS = {'@a.': 'addressing attribute', '@c.': 'computational attribute', '@s.': 'state variable'}


def parse(lexer_class, parser_class, rule: str, text: str):
    """The tree of a text by one entry rule of a grammar, and its syntax errors."""
    lexer = lexer_class(InputStream(text))
    parser = parser_class(CommonTokenStream(lexer))
    # Collect syntax errors rather than print them
    errors = SyntaxErrors()
    for recognizer in (lexer, parser):
        recognizer.removeErrorListeners()
        recognizer.addErrorListener(errors)
    return getattr(parser, rule)(), errors.found


def strings(instruction: str, what: str, given: Sequence[str]) -> List[str]:
    """A copy of a list of strings; one bare string is refused."""
    if isinstance(given, str):
        raise TypeError(f'{instruction}: {what} takes a list of strings, not one string')
    return list(given)


def term(expr) -> str:
    """One start or size as a constraint term, bracketed unless a single token."""
    text = str(expr).strip()
    return text if re.fullmatch(r'@?[\w.]+', text) else f'({text})'
