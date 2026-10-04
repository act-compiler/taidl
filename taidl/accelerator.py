"""Main Accelerator class for TAIDLv2"""

import os
import inspect
from dataclasses import dataclass, field
from typing import List, Sequence

from .data_model import Constant, DataModel
from .instruction import Instruction


@dataclass
class Accelerator:
    name: str
    data_model: List[DataModel]
    state: List[Constant]
    instructions: List[Instruction] = field(init=False)
    base_dir: str = field(init=False)

    def __init__(self, name: str, base_dir: str = None):
        self.name = name.replace(' ', '_')
        self.instructions = []
        self.state = []
        self.data_model = []
        if base_dir is not None:
            self.base_dir = base_dir
        else:
            caller_file = inspect.stack()[1].filename
            if os.path.exists(caller_file):
                self.base_dir = os.path.dirname(os.path.abspath(caller_file))
            else:
                self.base_dir = os.getcwd()
        self.add_data_model('d0', [], [], 'u8')

    def add_data_model(
        self, name: str, dimensions: List[int], unit_dim: List[int], var_type: str
    ) -> None:
        self.data_model.append(DataModel(name, dimensions, unit_dim, var_type))

    def add_initial_state(self, name: str, value: int) -> None:
        """Declare a machine state variable, @s.<name>, with its initial value."""
        self.state.append(Constant(name, value))

    def add_instruction(
        self,
        name: str,
        computation_attr: List[str],
        addressing_attr: List[str],
        *,
        update: Sequence[str] = (),
        constraints: Sequence[str] = (),
    ) -> Instruction:
        new_instruction = Instruction(
            name,
            computation_attr,
            addressing_attr,
            constraints,
            update,
            self.data_model,
        )
        self.instructions.append(new_instruction)
        return new_instruction
