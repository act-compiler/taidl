"""Instruction set definitions for TAIDLv2"""

from dataclasses import dataclass
from typing import List

from .data_model import DataModel
from .template import generate_code, templates, indent_code

# Import semantic generator for ANTLR4-based parsing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generators', 'oracle'))
from semantic_generator import generate_semantic_code


def blind_substitute(input: str) -> str:
    output = input.replace("@c.", "attrs['")
    output = output.replace("@a.", "attrs['")
    output = output.replace("@s.", "state['")

    output = output.replace("]", "']")
    return output


@dataclass
class Instruction:
    instruction: str
    comp_attr: List[str]
    parameters: List[str]
    constraints: List[str]
    data_models: List[DataModel]
    cost: str
    update: List[str]
    inputs: str
    outputs: str
    semantics: str

    # Storing input/output in same format as when they were set
    instr_inputs: List[List[str]]
    instr_outputs: List[List[str]]
    instr_semantics: str

    def __init__(self, instruction: str, comp_attr: List[str], addr_attr: List[str], constraints: List[str], cost: str, update: List[str], data_models: List[DataModel]):
        self.instruction = instruction.replace(" ", "_")
        self.comp_attr = comp_attr
        self.parameters = addr_attr
        self.constraints = constraints
        self.cost = cost
        self.update = update
        self.data_models = data_models
        self.semantics = "\tpass\n"
        self.inputs = ""
        self.outputs = ""

    def generate_api_function(self) -> str:
        attr_list = ",".join(self.comp_attr + self.parameters)
        func_name = self.instruction

        set_attributes = ""
        for attr in self.parameters:
            set_attributes += f'\t"{attr}": {attr},\n'
        set_attributes = indent_code(set_attributes)

        set_comp_attr = ""
        for attr in self.comp_attr:
            set_comp_attr += f'\t"{attr}": {attr},\n'
        set_comp_attr = indent_code(set_comp_attr)

        constraints = ""
        for idx, line in enumerate(self.constraints):
            constraints += f'#f{idx} = (' + line + ')\n'
        for idx, line in enumerate(self.constraints):
            if idx == 0:
                constraints += f'\n#flag = f{idx} '
            else:
                constraints += f'and f{idx} '

        update = ""
        for line in self.update:
            update += '\n' + line
        cost = self.cost
        fsim = "pass"

        # Ensure newlines between sections to prevent syntax errors
        parts = []
        if self.inputs:
            parts.append(self.inputs)
        if self.semantics:
            parts.append(self.semantics)
        if self.outputs:
            parts.append(self.outputs)
        fsim_compile = '\n'.join(parts)

        output = generate_code(templates["API_FUNC"], {
            "attributes": attr_list,
            "func_name": func_name,
            "update": update,
            "cost": cost,
            "constraints": constraints,
            "fsim": fsim,
            "fsim_compile": fsim_compile,
            "set_attributes": set_attributes,
            "set_comp_attr": set_comp_attr
        })

        func_def = f'def {func_name}({attr_list}) -> None:\n'
        output = func_def + indent_code(output)

        return output

    def generate_cost_function(self) -> str:
        output = f'\ndef {self.instruction}_cost(attrs, state):\n'
        output += ('\tcost = ' + self.cost)
        output += '\n\treturn cost'
        return output

    def generate_update_function(self) -> str:
        output = f'\ndef {self.instruction}_update(attrs, state):'
        for line in self.update:
            output += '\n\t' + line
        output += '\n\treturn state\n'
        return output

    def generate_constraint_function(self) -> str:
        output = f'\ndef {self.instruction}_constraints(attrs, state, constants):'
        output += f'\n\tif list(attrs.keys()) != ['

        for attribute in self.parameters:
            output += f'"{attribute}",'
        output += "]:\n\t\treturn False"

        if (len(self.constraints) == 0):
            output += '\n\treturn True'
            return output

        for idx, line in enumerate(self.constraints):
            output += f'\n\tf{idx} = (' + line + ')'
        output += '\n'
        for idx, line in enumerate(self.constraints):
            if idx == 0:
                output += f'\n\tflag = f{idx} '
            else:
                output += f'and f{idx} '
        output += '\n\treturn flag'
        return output

    def find_data_model(self, name: str) -> DataModel:
        for model in self.data_models:
            if (model.var_name == name):
                break
        else:
            model = None
        assert (model != None), f"Data buffer '{name}' not found"
        return model

    def set_inputs(self, input: List[List[any]]):
        """Generate input loading code directly without regex parsing"""
        self.instr_inputs = input
        output = ""

        for counter, slice_spec in enumerate(input, start=1):
            assert len(slice_spec) == 3, "Wrong input slice formatting."

            buffer_name = slice_spec[0]
            start_indices = slice_spec[1]
            shapes = slice_spec[2]

            model = self.find_data_model(buffer_name)

            # Build size list (shapes + unit dimensions)
            size_list = [f"'{s}'" for s in shapes]
            for unit_dim in model.unit_dim:
                size_list.append(f"'{unit_dim}'")

            # Build slice configs (start:start+shape for each dimension)
            slice_configs = []
            for start, shape in zip(start_indices, shapes):
                slice_configs.append(f"'{start}:{start}+{shape}'")
            for unit_dim in model.unit_dim:
                slice_configs.append(f"'0:{unit_dim}'")

            # Generate code using template
            mapping = {
                "rhs_name": f"'{buffer_name}'",
                "lhs": f"'In{counter}'",
                "type": f"'{model.var_type}'",
                "size": "[" + ",".join(size_list) + "]",
                "slice": "[" + ",".join(slice_configs) + "]"
            }
            output += generate_code(templates["SLICE_LOAD"], mapping)

        self.inputs = indent_code(output) if output else ""

    def set_outputs(self, output: List[List[str]]):
        """Generate output storing code directly without regex parsing"""
        self.instr_outputs = output
        code_output = ""

        for counter, slice_spec in enumerate(output):
            assert len(slice_spec) == 3, "Wrong output slice formatting."

            buffer_name = slice_spec[0]
            start_indices = slice_spec[1]
            # shapes not used for output, only start indices

            model = self.find_data_model(buffer_name)

            # Build start_indices list (includes unit dimension indices)
            start_list = [f"'{idx}'" for idx in start_indices]
            for _ in model.unit_dim:
                start_list.append("'0'")

            # Generate code using template
            mapping = {
                "lhs": f"'Out{counter}'",
                "rhs_name": f"'{buffer_name}'",
                "slice": "[" + ",".join(start_list) + "]"
            }
            code_output += generate_code(templates["SLICE_STORE"], mapping)

        self.outputs = indent_code(code_output) if code_output else ""

    def add_semantics(self, input: str):
        """Add instruction semantics using ANTLR4 parsing"""
        self.instr_semantics = input
        # Parse semantics using ANTLR4 and generate Python code
        self.semantics = generate_semantic_code(input)

    def add_constraints(self, input: str):
        input = blind_substitute(input.strip())
        input = input.split("\n")
        input = [line for line in input if line.strip()]
        self.constraints = input

    def generate_semantic_function(self) -> str:
        output = f'\ndef {self.instruction}_semantics(attrs, state, global_counters):\n'
        output += '\toutput = []\n\tlvars={}\n'
        output += self.inputs
        output += self.semantics
        output += self.outputs
        output += '\treturn output\n'
        return output
