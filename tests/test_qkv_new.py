"""Tests for QKV_new ISA spec parsing"""

import importlib.util
import os

import pytest
from taidl.antlr4 import IDLV2Parser

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")

spec = importlib.util.spec_from_file_location("QKV_new", os.path.join(EXAMPLES_DIR, "QKV_new.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
qkv = module.qkv


@pytest.mark.incremental
class TestQKVNew:
    def test_accelerator_name(self):
        assert qkv.name == "QKV"

    def test_data_models(self):
        names = [dm.var_name for dm in qkv.data_model]
        assert "d0" in names
        assert "d1" in names
        assert "d2" in names
        assert "d3" in names

    def test_data_model_d3(self):
        d3 = next(dm for dm in qkv.data_model if dm.var_name == "d3")
        assert d3.access_dim == [128]
        assert d3.unit_dim == [64]
        assert d3.var_type == "bf16"

    def test_instruction_count(self):
        assert len(qkv.instructions) == 10

    def test_instruction_names(self):
        names = [i.instruction for i in qkv.instructions]
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
        for instr in qkv.instructions:
            assert instr.instr_semantics_ast is not None
            assert isinstance(instr.instr_semantics_ast, IDLV2Parser.ModuleContext)

    def test_transpose_has_no_comp_attr(self):
        transpose = next(i for i in qkv.instructions if i.instruction == "transpose_13")
        assert transpose.comp_attr == []

    def test_gemm_33_inputs(self):
        gemm = next(i for i in qkv.instructions if i.instruction == "gemm_33")
        assert len(gemm.instr_inputs) == 2
        assert gemm.instr_inputs[0][0] == "d3"
        assert gemm.instr_inputs[1][0] == "d3"

    def test_gemm_13_inputs(self):
        gemm = next(i for i in qkv.instructions if i.instruction == "gemm_13")
        assert gemm.instr_inputs[0][0] == "d1"
        assert gemm.instr_inputs[1][0] == "d3"
