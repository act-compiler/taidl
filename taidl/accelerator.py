import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .template import *
from .utils import *

BASE_DIR = os.getcwd()


@dataclass
class Constant:
    const_name: str
    value: int


@dataclass
class DataModel:
    var_name: str
    var_dim: List[str]
    var_type: str
    array_dim_str: str = field(init=False)
    num_dim_str: str = field(init=False)

    def create_arr_str(self) -> str:
        output = '['
        for dim in self.var_dim:
            output += f"'{dim}',"
        output = output[:-1]
        output += ']'
        return output

    def create_num_str(self) -> str:
        output = '{'
        for i in range(len(self.var_dim) - 1, -1, -1):
            if (i == 0):
                output += str(i)
            else:
                output += str(i) + ","
        output += "}"
        return output

    def __init__(self, var_name: str, var_dim: List[str], var_type: str = "s8"):
        self.var_name = var_name
        self.var_dim = var_dim
        self.var_type = var_type
        self.array_dim_str = self.create_arr_str()
        self.num_dim_str = self.create_num_str()


@dataclass
class Instruction:
    instruction: str
    parameters: List[str]
    constraints: List[str]
    update: List[str]
    semantics: str

    def __init__(
            self,
            instruction: str,
            parameters: List[str],
            constraints: List[str],
            update: List[str]):
        self.instruction = instruction.replace(" ", "_")
        self.parameters = parameters
        self.constraints = constraints
        self.update = update
        self.semantics = "\tpass\n"

    def update_replace(self, s: str) -> str:
        s = re.sub(r'@s\.([a-zA-Z_][a-zA-Z0-9_]*)', r'state["\1"]', s)
        s = re.sub(r'@a\.([a-zA-Z_][a-zA-Z0-9_]*)', r'attrs["\1"]', s)
        return s

    def generate_api_function(self) -> str:
        attr_list = ",".join(self.parameters)
        func_name = self.instruction

        set_attributes = ""
        for attr in self.parameters:
            set_attributes += f'\t"{attr}": {attr},\n'
        set_attributes = indent_code(set_attributes)

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
            update += '\n\t' + self.update_replace(line)
        fsim = "pass"

        fsim_compile = self.semantics

        output = generate_code(templates["API_FUNC"], {
            "attributes": attr_list,
            "func_name": func_name,
            "update": update,
            "constraints": constraints,
            "fsim": fsim,
            "fsim_compile": fsim_compile,
            "set_attributes": set_attributes
        })
        func_def = f'def {func_name}({attr_list}) -> None:\n'
        output = func_def + indent_code(output)
        return output

    def generate_block(self, lines):
        output = ""
        for line in lines:
            if (line["STATEMENT"] == "SLICE_LOAD"):
                output += generate_code(templates["SLICE_LOAD"], line)
            elif (line["STATEMENT"] == "SLICE_STORE"):
                output += generate_code(templates["SLICE_STORE"], line)
            elif (line["STATEMENT"] == "ASSIGNMENT"):
                output += generate_code(templates[line["func_name"]], line)
            else:
                output += generate_code(templates[line["STATEMENT"]], {
                    "config": line["CONFIG"]["config"],
                    "loop_var": line["CONFIG"]["loop_var"],
                    "loop_range": line["CONFIG"]["loop_range"],
                })
                output += self.generate_block(line["BODY"])
        output = indent_code(output)
        return output

    def add_semantics(self, input: str):
        lines = parse_input(input)
        output = self.generate_block(lines)
        self.semantics = output

    def add_constraints(self, input):
        if isinstance(input, str):
            input = blind_substitute(input.strip())
            input = input.split("\n")
            input = [line for line in input if line.strip()]
        self.constraints = input

    def add_update(self, update_list: List[str]):
        self.update = update_list


@dataclass
class Accelerator:
    name: str
    data_model: List[DataModel]
    state: List[Constant]
    instructions: List[Instruction] = field(init=False)

    def __init__(self, name: str):
        self.name = name.replace(" ", "_")
        self.instructions = []
        self.state = []
        self.data_model = []
        init_templates()

    def add_initial_state(self, state_name: str, value: int) -> None:
        self.state.append(Constant(state_name, value))

    def add_data_model(self, model_name: str, count: str, shape: str) -> None:
        parts = shape.split('x')
        counts = count.split('x')
        data_type = parts[-1]
        dimensions = counts + parts[:-1]
        self.data_model.append(DataModel(model_name, dimensions, data_type))

    def add_instruction(
            self,
            instruction: str,
            parameters: List[str],
            constraints: List[str] = [],
            update: List[str] = []) -> Instruction:
        new_instruction = Instruction(instruction, parameters, constraints, update)
        self.instructions.append(new_instruction)
        return new_instruction

    def generate_sim(self, sim_directory: str = "sim") -> str:
        init_templates()
        gen_directory = os.path.join(BASE_DIR, sim_directory)
        Path(gen_directory).mkdir(parents=True, exist_ok=True)

        semantic_init = self.__generate_semantic_init()

        state = ""
        for constant in self.state:
            state += "'" + constant.const_name + "': " + str(constant.value) + ",\n"

        output = generate_code(templates["API_FILE"], {
            "constants": "",
            "state": state,
            "semantic_init": semantic_init,
            "API_NAME": self.name
        })
        for instruction in self.instructions:
            output += instruction.generate_api_function()

        with open(CUR_DIR + "/utils.py", "r") as file:
            util_file = file.read()
        with open(CUR_DIR + "/decorator.txt", "r") as file:
            decorator_file = file.read()
        decorator_file = f'TARGET_NAME = "{self.name}"\n' + decorator_file

        write_file(output, gen_directory + "/api.py")
        write_file(util_file, gen_directory + "/utils.py")
        write_file(decorator_file, gen_directory + "/decorator.py")

        print(f"Generated {self.name} TAIDL-TO API")

    def __generate_semantic_init(self) -> str:
        init_templates()
        template_semantic_init = templates["SEMANTIC_INIT"]
        template_semantic_counter = templates["SEMANTIC_COUNTER"]
        template_prologue_init = templates["PROLOGUE_INIT"]

        counters = ""
        prologue = ""
        for model in self.data_model:
            dimensions = model.array_dim_str.replace("'", "")
            mapping = {
                "var_name": model.var_name,
                "var_type": model.var_type,
                "var_dim": dimensions,
                "var_num": model.num_dim_str
            }
            counters += generate_code(template_semantic_counter, mapping)
            prologue += generate_code(template_prologue_init, mapping)

        counters = indent_code(counters, level=2)

        output = generate_code(template_semantic_init, {
            "custom_counters": counters,
            "custom_prologue": prologue
        })
        return output
