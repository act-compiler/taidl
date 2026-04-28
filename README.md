# TAIDL: Tensor Accelerator ISA Definition Language

TAIDL is a domain-specific language designed to define instruction set architectures (ISAs) for tensor accelerators. It provides a flexible and extensible framework for specifying the operations, data types, and memory models of tensor accelerators.

TAIDL is an integral part of the [ACT Ecosystem](https://github.com/act-compiler/act), enabling automated generation of:

- **Test Oracles**, a.k.a. functional simulators ([act-compiler/act-oracle](https://github.com/act-compiler/act-oracle))
- **Compiler Backends** ([act-compiler/act-backend](https://github.com/act-compiler/act-backend))

TAIDL is published in [MICRO 2025](https://doi.org/10.1145/3725843.3756075). For detailed evaluations, please refer to our [MICRO 2025 Artifact](https://github.com/act-compiler/taidl-artifact-micro25).

## Installation

```bash
pip install git+https://github.com/act-compiler/taidl.git@v2.2
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
pip install -e .
pip install pytest
pytest tests/
```

## Implementation Details

TAIDL is a pure data model + language parser. It stores:

- Accelerator metadata (name, constants, state)
- Data model definitions (memory spaces with dimensions and types)
- Instruction definitions (parameters, constraints, inputs/outputs)
- Parsed semantics AST (ANTLR4 parse tree)

Generators (TAIDL-TO, ACT-Backend) consume the `Accelerator` object and its pre-parsed ASTs to produce target-specific software tools.
