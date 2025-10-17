"""Main Accelerator class for TAIDLv2"""

from dataclasses import dataclass, field
from typing import List
from pathlib import Path
import os
import shutil

from .data_model import Constant, DataModel
from .instruction import Instruction
from .template import init_templates, templates, generate_code, write_file, indent_code


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class InstructionMetadata:
    name: str
    semantics: str
    has_comp_attrs: bool
    rhs_size: int


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
        init_templates()
        self.add_data_model("d0", [], [], "u8")

    def add_data_model(self, model_name: str, dimensions: List[str], unit_dim: List[str], var_type: str) -> None:
        self.data_model.append(DataModel(model_name, dimensions, unit_dim, var_type))

    def add_instruction(self, instruction: str, computation_attr: List[str], addressing_attr: List[str], cost: str = "0", update: List[str] = [], constraints: List[str] = []) -> Instruction:
        new_instruction = Instruction(instruction, computation_attr,
                                      addressing_attr, constraints, cost, update, self.data_model)
        self.instructions.append(new_instruction)
        return new_instruction

    def generate_oracle(self) -> str:
        """Generate Oracle API code"""
        from generators.oracle.generator import generate_oracle

        generate_oracle(
            accelerator_name=self.name,
            instructions=self.instructions,
            constants=self.constants,
            state=self.state,
            data_models=self.data_model,
            base_dir=BASE_DIR
        )

    def __generate_semantic_init(self) -> str:
        init_templates()
        template_semantic_init = templates["SEMANTIC_INIT"]
        template_semantic_counter = templates["SEMANTIC_COUNTER"]
        template_prologue_init = templates["PROLOGUE_INIT"]

        counters = ""
        prologue = ""
        for model in self.data_model:
            if (model.var_name == 'd0'):
                continue
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

    def _get_instruction_metadata(self) -> List[InstructionMetadata]:
        """Extract instruction metadata for code generation"""
        metadata_list = []
        for instruction in self.instructions:
            if hasattr(instruction, 'instr_semantics') and instruction.instr_semantics:
                metadata = InstructionMetadata(
                    name=instruction.instruction,
                    semantics=instruction.instr_semantics,
                    has_comp_attrs=len(instruction.comp_attr) > 0,
                    rhs_size=len(instruction.instr_inputs) + 1
                )
                metadata_list.append(metadata)
        return metadata_list

    def generate_backend(self) -> None:
        """Generate ACT backend code"""
        from generators.backend.generator import generate_backend

        instruction_metadata = self._get_instruction_metadata()
        generate_backend(
            accelerator_name=self.name,
            instructions=self.instructions,
            data_models=self.data_model,
            instruction_metadata=instruction_metadata,
            base_dir=BASE_DIR
        )
