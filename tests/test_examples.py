import importlib.util
import os

import pytest

from taidl.antlr4 import IDLV2Parser

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')

ADDRESSES = ['addr_in', 'addr_out']
OPERANDS = ['addr_1', 'addr_2', 'addr_out']

# Per example: models' dims and types, instructions' attributes and buffers
EXAMPLES = {
    'mini_trn': {
        'models': {
            'd0': ([], [], 'u8'),
            'd1': ([128], [64], 'bf16'),
            'd2': ([64], [64], 'bf16'),
        },
        'instructions': {
            'load_rm': (['n'], ADDRESSES, ['d0'], ['d1']),
            'load_cm': (['n'], ADDRESSES, ['d0'], ['d1']),
            'store_rm': (['n'], ADDRESSES, ['d1'], ['d0']),
            'store_cm': (['n'], ADDRESSES, ['d1'], ['d0']),
            'mov': (['n'], ADDRESSES, ['d2'], ['d1']),
            'gemm': ([], OPERANDS, ['d1', 'd1'], ['d2']),
            'softmax': (['n'], ['addr'], ['d2'], ['d2']),
        },
    },
    'mini_trn_double': {
        'models': {
            'd0': ([], [], 'u8'),
            'd1': ([128], [64], 'bf16'),
            'd3': ([128], [64], 'bf16'),
            'd2': ([64], [64], 'bf16'),
        },
        'instructions': {
            'load_01': (['n'], ADDRESSES, ['d0'], ['d1']),
            'load_03': (['n'], ADDRESSES, ['d0'], ['d3']),
            'store_10': (['n'], ADDRESSES, ['d1'], ['d0']),
            'store_30': (['n'], ADDRESSES, ['d3'], ['d0']),
            'transpose_13': ([], ADDRESSES, ['d1'], ['d3']),
            'mov_21': (['n'], ADDRESSES, ['d2'], ['d1']),
            'mov_23': (['n'], ADDRESSES, ['d2'], ['d3']),
            'gemm_33': ([], OPERANDS, ['d3', 'd3'], ['d2']),
            'gemm_13': ([], OPERANDS, ['d1', 'd3'], ['d2']),
            'softmax': (['n'], ['addr'], ['d2'], ['d2']),
        },
    },
}


@pytest.fixture(scope='module', params=list(EXAMPLES))
def example(request):
    """One example's accelerator, with what the example declares."""
    path = os.path.join(EXAMPLES_DIR, f'{request.param}.py')
    spec = importlib.util.spec_from_file_location(request.param, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, request.param), EXAMPLES[request.param]


class TestExamples:
    def test_accelerator_name(self, example):
        acc, declared = example
        assert EXAMPLES[acc.name] is declared

    def test_data_models(self, example):
        acc, declared = example
        models = {m.var_name: (m.access_dim, m.unit_dim, m.var_type) for m in acc.data_model}
        assert models == declared['models']
        assert list(models) == list(declared['models'])

    def test_instructions(self, example):
        acc, declared = example
        instructions = {
            instr.instruction: (
                instr.comp_attr,
                instr.parameters,
                [region[0] for region in instr.instr_inputs],
                [region[0] for region in instr.instr_outputs],
            )
            for instr in acc.instructions
        }
        assert instructions == declared['instructions']
        assert list(instructions) == list(declared['instructions'])

    def test_every_semantics_parsed(self, example):
        acc = example[0]
        for instr in acc.instructions:
            assert isinstance(instr.instr_semantics_ast, IDLV2Parser.ModuleContext)
