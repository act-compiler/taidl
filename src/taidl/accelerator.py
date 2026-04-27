"""Main Accelerator class for TAIDLv2"""

from dataclasses import dataclass, field
from typing import List

from .data_model import Constant, DataModel
from .instruction import Instruction


@dataclass
class Accelerator:
    name: str
    constants: List[Constant]
    data_model: List[DataModel]
    state: List[Constant]
    instructions: List[Instruction] = field(init=False)

    def __init__(self, name: str):
        self.name = name.replace(" ", "_")
        self.constants = []
        self.instructions = []
        self.state = []
        self.data_model = []
        self.add_data_model("d0", [], [], "u8")

    def add_data_model(self, model_name: str, dimensions: List[str], unit_dim: List[str], var_type: str) -> None:
        self.data_model.append(DataModel(model_name, dimensions, unit_dim, var_type))

    def add_instruction(self, instruction: str, computation_attr: List[str], addressing_attr: List[str], cost: str = "0", update: List[str] = [], constraints: List[str] = []) -> Instruction:
        new_instruction = Instruction(instruction, computation_attr,
                                      addressing_attr, constraints, cost, update, self.data_model)
        self.instructions.append(new_instruction)
        return new_instruction
