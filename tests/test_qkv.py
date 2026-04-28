"""Tests for QKV ISA spec parsing"""

import importlib.util
import os

import pytest
from taidl.antlr4 import IDLV2Parser

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")

spec = importlib.util.spec_from_file_location("QKV", os.path.join(EXAMPLES_DIR, "QKV.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
qkv = module.qkv


@pytest.mark.incremental
class TestQKV:
    def test_accelerator_name(self):
        assert qkv.name == "QKV"

    def test_data_models(self):
        names = [dm.var_name for dm in qkv.data_model]
        assert "d0" in names
        assert "d1" in names
        assert "d2" in names

    def test_data_model_d1(self):
        d1 = next(dm for dm in qkv.data_model if dm.var_name == "d1")
        assert d1.access_dim == [128]
        assert d1.unit_dim == [64]
        assert d1.var_type == "bf16"

    def test_instruction_count(self):
        assert len(qkv.instructions) == 7

    def test_instruction_names(self):
        names = [i.instruction for i in qkv.instructions]
        assert "load_rm" in names
        assert "load_cm" in names
        assert "store_rm" in names
        assert "store_cm" in names
        assert "mov" in names
        assert "gemm" in names
        assert "softmax" in names

    def test_all_semantics_parsed(self):
        for instr in qkv.instructions:
            assert instr.instr_semantics_ast is not None
            assert isinstance(instr.instr_semantics_ast, IDLV2Parser.ModuleContext)

    def test_gemm_attributes(self):
        gemm = next(i for i in qkv.instructions if i.instruction == "gemm")
        assert gemm.comp_attr == []
        assert gemm.parameters == ["addr_1", "addr_2", "addr_out"]

    def test_load_rm_attributes(self):
        load_rm = next(i for i in qkv.instructions if i.instruction == "load_rm")
        assert load_rm.comp_attr == ["n"]
        assert load_rm.parameters == ["addr_in", "addr_out"]

    def test_inputs_outputs(self):
        gemm = next(i for i in qkv.instructions if i.instruction == "gemm")
        assert len(gemm.instr_inputs) == 2
        assert len(gemm.instr_outputs) == 1

    def test_softmax_is_inplace(self):
        softmax = next(i for i in qkv.instructions if i.instruction == "softmax")
        assert softmax.instr_inputs[0][0] == "d2"
        assert softmax.instr_outputs[0][0] == "d2"
