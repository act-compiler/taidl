"""Instruction set definitions for TAIDLv2"""

from dataclasses import dataclass
from typing import List

from .data_model import DataModel


@dataclass
class Instruction:
    instruction: str
    comp_attr: List[str]
    parameters: List[str]
    constraints: List[str]
    data_models: List[DataModel]
    cost: str
    update: List[str]

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
        self.instr_inputs = []
        self.instr_outputs = []
        self.instr_semantics = ""

    def find_data_model(self, name: str) -> DataModel:
        for model in self.data_models:
            if (model.var_name == name):
                break
        else:
            model = None
        assert (model != None), f"Data buffer '{name}' not found"
        return model

    def set_inputs(self, inputs: List[List]):
        self.instr_inputs = inputs

    def set_outputs(self, outputs: List[List[str]]):
        self.instr_outputs = outputs

    def add_semantics(self, semantics: str):
        self.instr_semantics = semantics

    def add_constraints(self, constraints: str):
        lines = constraints.strip().split("\n")
        self.constraints = [line for line in lines if line.strip()]
