"""Tests that the example ISA specs parse and load correctly"""

import importlib.util
import os
import sys

import pytest
from taidl import Accelerator
from taidl.antlr4 import IDLV2Parser


EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


def load_example(filename: str):
    """Load an example ISA spec file and return its module"""
    filepath = os.path.join(EXAMPLES_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="class")
def qkv_module():
    return load_example("QKV.py")


@pytest.fixture(scope="class")
def qkv_new_module():
    return load_example("QKV_new.py")


@pytest.mark.incremental
class TestQKV:
    @pytest.fixture(autouse=True)
    def setup(self, qkv_module):
        self.qkv = qkv_module.qkv

    def test_accelerator_name(self):
        assert self.qkv.name == "QKV"

    def test_data_models(self):
        names = [dm.var_name for dm in self.qkv.data_model]
        assert "d0" in names
        assert "d1" in names
        assert "d2" in names

    def test_data_model_d1(self):
        d1 = next(dm for dm in self.qkv.data_model if dm.var_name == "d1")
        assert d1.access_dim == [128]
        assert d1.unit_dim == [64]
        assert d1.var_type == "bf16"

    def test_instruction_count(self):
        assert len(self.qkv.instructions) == 7

    def test_instruction_names(self):
        names = [i.instruction for i in self.qkv.instructions]
        assert "load_rm" in names
        assert "load_cm" in names
        assert "store_rm" in names
        assert "store_cm" in names
        assert "mov" in names
        assert "gemm" in names
        assert "softmax" in names

    def test_all_semantics_parsed(self):
        for instr in self.qkv.instructions:
            assert instr.instr_semantics_ast is not None
            assert isinstance(instr.instr_semantics_ast, IDLV2Parser.ModuleContext)

    def test_gemm_attributes(self):
        gemm = next(i for i in self.qkv.instructions if i.instruction == "gemm")
        assert gemm.comp_attr == []
        assert gemm.parameters == ["addr_1", "addr_2", "addr_out"]

    def test_load_rm_attributes(self):
        load_rm = next(i for i in self.qkv.instructions if i.instruction == "load_rm")
        assert load_rm.comp_attr == ["n"]
        assert load_rm.parameters == ["addr_in", "addr_out"]

    def test_inputs_outputs(self):
        gemm = next(i for i in self.qkv.instructions if i.instruction == "gemm")
        assert len(gemm.instr_inputs) == 2
        assert len(gemm.instr_outputs) == 1

    def test_softmax_is_inplace(self):
        softmax = next(i for i in self.qkv.instructions if i.instruction == "softmax")
        assert softmax.instr_inputs[0][0] == "d2"
        assert softmax.instr_outputs[0][0] == "d2"


@pytest.mark.incremental
class TestQKVNew:
    @pytest.fixture(autouse=True)
    def setup(self, qkv_new_module):
        self.qkv = qkv_new_module.qkv

    def test_accelerator_name(self):
        assert self.qkv.name == "QKV"

    def test_data_models(self):
        names = [dm.var_name for dm in self.qkv.data_model]
        assert "d0" in names
        assert "d1" in names
        assert "d2" in names
        assert "d3" in names

    def test_data_model_d3(self):
        d3 = next(dm for dm in self.qkv.data_model if dm.var_name == "d3")
        assert d3.access_dim == [128]
        assert d3.unit_dim == [64]
        assert d3.var_type == "bf16"

    def test_instruction_count(self):
        assert len(self.qkv.instructions) == 10

    def test_instruction_names(self):
        names = [i.instruction for i in self.qkv.instructions]
        assert "load_01" in names
        assert "load_03" in names
        assert "store_10" in names
        assert "store_30" in names
        assert "transpose_13" in names
        assert "mov_21" in names
        assert "mov_23" in names
        assert "gemm_33" in names
        assert "gemm_13" in names
        assert "softmax" in names

    def test_all_semantics_parsed(self):
        for instr in self.qkv.instructions:
            assert instr.instr_semantics_ast is not None
            assert isinstance(instr.instr_semantics_ast, IDLV2Parser.ModuleContext)

    def test_transpose_has_no_comp_attr(self):
        transpose = next(i for i in self.qkv.instructions if i.instruction == "transpose_13")
        assert transpose.comp_attr == []

    def test_gemm_33_inputs(self):
        gemm = next(i for i in self.qkv.instructions if i.instruction == "gemm_33")
        assert len(gemm.instr_inputs) == 2
        assert gemm.instr_inputs[0][0] == "d3"
        assert gemm.instr_inputs[1][0] == "d3"

    def test_gemm_13_inputs(self):
        gemm = next(i for i in self.qkv.instructions if i.instruction == "gemm_13")
        assert gemm.instr_inputs[0][0] == "d1"
        assert gemm.instr_inputs[1][0] == "d3"
