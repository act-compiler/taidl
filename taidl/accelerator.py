"""Main Accelerator class for TAIDLv2"""

import os
import inspect
from typing import List, Sequence

from .data_model import TYPES, DataModel, State
from .instruction import Instruction
from .names import check_name


class Accelerator:
    name: str
    data_model: List[DataModel]
    state: List[State]
    instructions: List[Instruction]
    base_dir: str

    def __init__(self, name: str, base_dir: str | None = None):
        check_name('accelerator', name)
        self.name = name
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
        check_name('data model', name, taken=[model.var_name for model in self.data_model])
        for what, dims in (('dimensions', dimensions), ('unit_dim', unit_dim)):
            if not isinstance(dims, (list, tuple)) or any(
                type(dim) is not int or dim < 1 for dim in dims
            ):
                raise ValueError(f'{name}: {what} {dims!r} is not a list of positive integers')
        if var_type not in TYPES:
            raise ValueError(f"{name}: type '{var_type}' is not one of {', '.join(TYPES)}")
        self.data_model.append(DataModel(name, dimensions, unit_dim, var_type))

    def add_initial_state(self, name: str, value: int) -> None:
        """Declare a machine state variable, @s.<name>, with its initial value."""
        # State belongs with the data models
        if self.instructions:
            raise ValueError(
                f"state '{name}' follows an instruction: "
                'state is declared with the data models, before the instructions'
            )
        check_name('state', name, taken=[state.name for state in self.state])
        if type(value) is not int:
            raise ValueError(f"state '{name}': value {value!r} is not an integer")
        self.state.append(State(name, value))

    def add_instruction(
        self,
        name: str,
        computation_attr: List[str],
        addressing_attr: List[str],
        *,
        update: Sequence[str] = (),
        constraints: Sequence[str] = (),
    ) -> Instruction:
        check_name('instruction', name, taken=[instr.instruction for instr in self.instructions])
        new_instruction = Instruction(
            name,
            computation_attr,
            addressing_attr,
            constraints,
            update,
            self.data_model,
            self.state,
        )
        self.instructions.append(new_instruction)
        return new_instruction
