# TAIDL: Tensor Accelerator ISA Definition Language

TAIDL is a domain-specific language designed to define instruction set architectures (ISAs) for tensor accelerators. It provides a flexible and extensible framework for specifying the operations, data types, and memory models of tensor accelerators.

TAIDL is an integral part of the [ACT Ecosystem](https://github.com/act-compiler/act), enabling automated generation of:

- **Test Oracles**, a.k.a. functional simulators ([act-compiler/act-oracle](https://github.com/act-compiler/act-oracle))
- **Compiler Backends** ([act-compiler/act-backend](https://github.com/act-compiler/act-backend))

TAIDL is published in [MICRO 2025](https://doi.org/10.1145/3725843.3756075). For detailed evaluations, please refer to our [MICRO 2025 Artifact](https://github.com/act-compiler/taidl-artifact-micro25).

## Installation

TAIDL needs Python 3.14 or later.

```bash
pip install git+https://github.com/act-compiler/taidl.git@v2.10
```

For development:

```bash
git clone https://github.com/act-compiler/taidl.git
cd taidl
pip install -e .
```

## Examples

- `QKV.py` — QKV attention accelerator
- `QKV_new.py` — variant of QKV

## Testing

```bash
./tests/pytest.sh
```

`tests/pytest.sh` runs the tests in `devanshdvj/act-env:py3.14-jax0.10.2`, the image `docker/act.env` names, in its tag for the host's architecture, amd64 or arm64.

## Specs

A spec is a Python program that builds an `Accelerator`: its data models, then its instructions.

```python
from taidl import Accelerator

acc = Accelerator('Demo')

# d1: 128 rows of 64 bf16 values
acc.add_data_model('d1', [128], [64], 'bf16')

# load: n rows from the off-chip memory into d1
instr = acc.add_instruction('load', ['n'], ['addr_in', 'addr_out'])
instr.set_inputs([['d0', ['@a.addr_in'], ['@c.n * 128']]])
instr.set_outputs([['d1', ['@a.addr_out'], ['@c.n']]])
instr.add_semantics("""
ENTRY {
    %In0 = u8[`@c.n * 128`] parameter(0);
    %a = u8[`@c.n`,64,2] reshape(%In0);
    ROOT %Out0 = bf16[`@c.n`,64] bitcast_convert(%a);
}
""")
```

The language is documented under `docs/`:

- `docs/declarations.md`: the accelerator, its data models, its regions and the names a spec gives
- `docs/instructions.md`: an instruction, its attributes, constraints, in-place and placement marks, and machine state
- `docs/semantics.md`: the text of a semantics, its types, shapes, operands and attributes, and what is refused
- `docs/expressions.md`: expressions, constraints and state updates
- `docs/operations.md`: the operation words, what each takes, and the operations that stay out

## Grammar

Instruction semantics are parsed by the ANTLR4 grammar `taidl/antlr4/IDLV2.g4`, and expressions, starts, sizes, constraints and updates by `taidl/antlr4/IDLV2Expr.g4`.
The lexer, parser, listener and visitor of each are generated from it and committed with it.
After editing a grammar, regenerate them with the ANTLR 4.9.2 tool, which matches the runtime pin:

```bash
ANTLR_JAR=/path/to/antlr-4.9.2-complete.jar ./taidl/antlr4/generate.sh
```

## Implementation Details

TAIDL is a pure data model + language parser. It stores:

- Accelerator metadata (name, state)
- Data model definitions (memory spaces with dimensions and types)
- Instruction definitions (parameters, constraints, inputs/outputs)
- Parsed semantics AST (ANTLR4 parse tree)

Generators (TAIDL-TO, ACT-Backend) consume the `Accelerator` object and its pre-parsed ASTs to produce target-specific software tools.
