# TAIDL: Tensor Accelerator ISA Definition Language

TAIDL is published in [MICRO 2025](https://doi.org/10.1145/3725843.3756075).

This repository contains the source code and documentation for TAIDL, a domain-specific language designed to define instruction set architectures (ISAs) for tensor accelerators. TAIDL aims to provide a flexible and extensible framework for specifying the operations, data types, and memory models of tensor accelerators, facilitating the design and implementation of efficient hardware and software solutions for machine learning workloads.

TAIDL not only standardizes the way tensor accelerator ISAs are specified but also enables automated generation of tools such as test oracles (functional simulators) and compiler backends, significantly reducing the effort required to develop and maintain these components.
The generated test oracles (called TAIDL-TOs) are orders of magnitude faster than existing functional simulators, making them suitable for large-scale testing and validation of tensor accelerator designs.

For detailed evaluations and comparisons, please refer to our [MICRO 2025 Artifact](https://github.com/act-compiler/taidl-artifact-micro25).

# Getting Started with TAIDL

## Writing Custom ISAs in TAIDL

Here, we provide a step-by-step guide to defining a custom ISA using TAIDL and writing kernels to run on the generated TAIDL-TO simulator.

First, launch our provided TAIDL docker environment using

```bash
./scripts/launch.sh
```

The TAIDL environment is at `/taidl/` in the Docker.

#### 1. Define Your ISA

Create a new `toy/` directory in `accelerators/` and define your ISA in `TAIDL_toy.py`:

```python
# accelerators/toy/TAIDL_toy.py
import importlib
import os
import sys

# Start: Import the TAIDL API #
repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(repo_dir))

Accelerator = importlib.import_module("taidl.accelerator").Accelerator
# End: Import the TAIDL API #

# Initialize a new accelerator instance
acc = Accelerator("Toy")

# Define data model (memory space)
acc.add_data_model("regs", "32", "16xs8")  # 32 registers with 16 elements each
# s8 indicates 8-bit signed integers

# Define instruction: load from HBM to register
instr = acc.add_instruction("load", ["dst", "addr"])
instr.add_semantics("""
%data:16xs8 <- hbm[@a.addr:@a.addr + 16];
%reshaped:1x16xs8 = reshape(%data);
%reshaped:1x16xs8 -> regs[@a.dst, 0];
""")

# Define instruction: store from register to HBM
instr = acc.add_instruction("store", ["src", "addr"])
instr.add_semantics("""
%data:1x16xs8 <- regs[@a.src:@a.src+1, 0:16];
%flattened:16xs8 = reshape(%data);
%flattened:16xs8 -> hbm[@a.addr];
""")

# Define instruction: add two registers
instr = acc.add_instruction("add", ["dst", "src1", "src2"])
instr.add_semantics("""
%a:1x16xs8 <- regs[@a.src1:@a.src1+1, 0:16];
%b:1x16xs8 <- regs[@a.src2:@a.src2+1, 0:16];
%c:1x16xs8 = add(%a, %b);
%c:1x16xs8 -> regs[@a.dst, 0];
""")

# Generate TAIDL-TO library
acc.generate_sim()
```

**Current directory structure**:

```
accelerators/toy/
└── TAIDL_toy.py             # ISA definition
```

#### 2. Generate Simulation Code

Run your TAIDL definition to generate the TAIDL-TO simulation library:

```bash
cd /taidl/accelerators/toy && python3 TAIDL_toy.py
```

This creates the `sim/` directory with:

- `api.py` - Operation APIs for your ISA
- `decorator.py` - Kernel compilation framework
- `utils.py` - Helper functions

**Current directory structure**:

```
accelerators/toy/
├── sim                      # Generated simulation code
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

#### 3. Write Kernels

Now, let's write kernels in `kernels.py` using your generated TAIDL-TO library:

```python
# accelerators/toy/kernels.py
import numpy as np
from sim import api
from sim.decorator import kernel


@kernel(hbm=1024,
        input=[
            {'addr': 0, 'shape': (16,), 'dtype': np.int8},
            {'addr': 16, 'shape': (16,), 'dtype': np.int8},
        ],
        output=[
            {'addr': 32, 'shape': (16,), 'dtype': np.int8},
        ])
def add_kernel():
    api.load(dst=0, addr=0)
    api.load(dst=1, addr=16)
    api.add(dst=2, src1=0, src2=1)
    api.store(src=2, addr=32)
```

**Current directory structure**:

```
accelerators/toy/
├── kernels.py               # New kernel: add_kernel
├── sim
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

#### 4. Test Your Kernels

Create a kernel runner `run_add.py` to execute and verify your kernel:

```python
# accelerators/toy/run_add.py
import numpy as np
from kernels import add_kernel
from sim.decorator import set_simulation_backend

# Generate random input data
np.random.seed(0)
a = np.random.randint(-40, 40, size=16, dtype=np.int8)
b = np.random.randint(-40, 40, size=16, dtype=np.int8)

print("A: \t", a)
print("B: \t", b)

# Compile the simulation
set_simulation_backend("CPU")
_, _ = add_kernel("fsim-compile")()

# Run the simulation
outputs, _ = add_kernel("fsim")(a, b)
print("Sum: \t", outputs[0])
```

Run the kernel to see the output:

```bash
cd /taidl/accelerators/toy && python3 run_add.py
```

**Expected output**:

```
A:       [  4 -30 -28   7   2  28 -17  -2 -18  15  24  36  -7  27  11  38]
B:       [ -6  27 -29 -31  -4  -7  -9 -19  -3  -4  15 -35  18   3  36  30]
Sum:     [ -2  -3 -57 -24  -2  21 -26 -21 -21  11  39   1  11  30  47  68]
```

**Current directory structure**:

```
accelerators/toy/
├── kernels.py
├── run_add.py               # Kernel runner
├── sim
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

#### 5. Debugging

TAIDL-TO allows you to inspect register and memory contents during kernel execution using the `api.debug()` function.

Now, edit the `add_kernel` to include debugging statements.

```python
# accelerators/toy/kernels.py
@kernel(hbm=1024, input=[...], output=[...])
def add_kernel():
    api.load(dst=0, addr=0)
    api.load(dst=1, addr=16)
    api.add(dst=2, src1=0, src2=1)
    api.debug(prefix="reg0", data="regs[0]")  # New code
    api.debug(prefix="result(reg2)", data="regs[2]")  # New code
    api.store(src=2, addr=32)
```

Run the kernel again to see the output along with debug information:

```bash
cd /taidl/accelerators/toy && python3 run_add.py
```

**Expected output**:

```
A:       [  4 -30 -28   7   2  28 -17  -2 -18  15  24  36  -7  27  11  38]
B:       [ -6  27 -29 -31  -4  -7  -9 -19  -3  -4  15 -35  18   3  36  30]
reg0:
shape: (1, 16)
[  [4, -30, -28, 7, 2, 28, -17, -2, -18, 15, 24, 36, -7, 27, 11, 38]]
result(reg2):
shape: (1, 16)
[  [-2, -3, -57, -24, -2, 21, -26, -21, -21, 11, 39, 1, 11, 30, 47, 68]]
Sum:     [ -2  -3 -57 -24  -2  21 -26 -21 -21  11  39   1  11  30  47  68]
```

Note that while the input variables `A` and `B` are 1-D tensors of shape `(16,)`, the debug output shows the register contents as 2-D tensor of shape `(1, 16)`.  
A register file is represented as a 2-D tensor of shape `(num_registers, elements_per_register)` with the first dimension indexing the registers (more details in the paper), with its slice `regs[0]` being a 2-D tensor of shape `(1, elements_per_register)`.  
This behavior is intended since scratchpads often access multiple rows at once, unlike traditional register files that access one register at a time.

**Current directory structure**:

```accelerators/toy/
├── kernels.py               # Edited kernel: add_kernel
├── run_add.py
├── sim
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

#### 6. Python native loops

Create a new kernel `loop_kernel` in `kernels.py` to add 50 vectors using a for loop.

```python
# accelerators/toy/kernels.py
@kernel(hbm=1024,
        input=[  # 50 vectors of 16 elements
            {'addr': 0, 'shape': (50, 16), 'dtype': np.int8},
        ],
        output=[  # Sum of the 50 vectors
            {'addr': 800, 'shape': (16,), 'dtype': np.int8},
        ])
def loop_kernel():
    api.load(dst=0, addr=0)  # Load first vector to initialize reg[0]

    for i in range(1, 50):              # Native for loop
        api.load(dst=1, addr=16 * i)    # Load vector i
        api.add(dst=0, src1=0, src2=1)  # Accumulate into dst=0

    api.store(src=0, addr=800)  # Store final accumulated result
```

Next, create a corresponding kernel runner `run_loop.py`:

```python
# accelerators/toy/run_loop.py
import numpy as np
from kernels import loop_kernel
from sim.decorator import set_simulation_backend

# Generate random input data: 50 vectors of 16 elements
np.random.seed(0)
vectors = np.random.randint(-2, 2, size=(50, 16), dtype=np.int8)

# Compile the simulation
set_simulation_backend("CPU")
_, compile_time = loop_kernel("fsim-compile")()

# Run the simulation
outputs, runtime = loop_kernel("fsim")(vectors)

golden = np.sum(vectors, axis=0)
print("Golden: \t", golden)
print("Result: \t", outputs[0])
assert np.array_equal(golden, outputs[0]), "Result does not match golden!"
print("Test passed!")

print("\nBenchmarking statistics:")
print(f"Compilation time: {compile_time:.3f} ms")
print(f"Simulation time: {runtime:.3f} ms")
```

Run the kernel to see the output:

```bash
cd /taidl/accelerators/toy && python3 run_loop.py
```

**Expected output**: (benchmarking statistics may vary based on your machine)

```
Golden:          [-13 -28 -14 -37 -19 -12 -18 -14 -23 -27 -27 -18 -30 -24 -34 -17]
Result:          [-13 -28 -14 -37 -19 -12 -18 -14 -23 -27 -27 -18 -30 -24 -34 -17]
Test passed!

Benchmarking statistics:
Compilation time: 116.406 ms
Simulation time: 12.657 ms
```

**Current directory structure**:

```accelerators/toy/
├── kernels.py               # New kernel: loop_kernel
├── run_add.py
├── run_loop.py              # New kernel runner: run_loop.py
├── sim
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

#### 7. TAIDL-TO loop API for faster compilation

We observed that using native Python loops can lead to slow compilation times for larger loop counts since the entire loop body is unrolled during compilation of the simulation.  
To address this, TAIDL-TO provides a loop API (`api.start_loop`, `api.end_loop`) that allows you to define loops that are handled directly by the simulator without unrolling.

Curious how these loops are implemented? Hint: XLA-HLO IR has a `while` loop operator that you can read about [here](https://openxla.org/xla/operation_semantics#while).

Now, edit the `loop_kernel` in `kernels.py` to use the TAIDL-TO loop API:

```python
# accelerators/toy/kernels.py
@kernel(hbm=1024, inputs=[...], outputs=[...])
def loop_kernel():
    api.load(dst=0, addr=0)  # Load first vector to initialize reg[0]

    api.start_loop("i", 1, 50)       # (End value is exclusive)
    api.load(dst=1, addr="16 * %i + 0")  # Load vector i
    api.add(dst=0, src1=0, src2=1)   # Accumulate into dst=0
    api.end_loop()

    api.store(src=0, addr=800)  # Store final accumulated result
```

Run the kernel again to see the output:

```bash
cd /taidl/accelerators/toy && python3 run_loop.py
```

**Expected output**: (benchmarking statistics may vary based on your machine)

```
Golden:          [-13 -28 -14 -37 -19 -12 -18 -14 -23 -27 -27 -18 -30 -24 -34 -17]
Result:          [-13 -28 -14 -37 -19 -12 -18 -14 -23 -27 -27 -18 -30 -24 -34 -17]
Test passed!

Benchmarking statistics:
Compilation time: 17.955 ms
Simulation time: 12.668 ms
```

You'll likely notice a significant speedup in compilation time compared to using native Python loops, especially as the loop count increases with little to no change in simulation time.

**Current directory structure**:

```accelerators/toy/
├── kernels.py               # Edited kernel: loop_kernel
├── run_add.py
├── run_loop.py
├── sim
│   ├── api.py
│   ├── decorator.py
│   └── utils.py
└── TAIDL_toy.py
```

## TAIDL API Reference

### Supported Operations

**Arithmetic Operations:**

- `add(A, B)` - Element-wise addition
- `subtract(A, B)` - Element-wise subtraction
- `multiply(A, B)` - Element-wise multiplication
- `divide(A, B)` - Element-wise division

**Math Functions:**

- `exp(A)` - Element-wise exponential
- `tanh(A)` - Element-wise hyperbolic tangent
- `maximum(A, B)` - Element-wise maximum
- `minimum(A, B)` - Element-wise minimum

**Logic Operations:**

- `xor(A, B)` - Bitwise XOR

**Shape Operations:**

- `reshape(A)` - Reshape tensor
- `transpose(A, dimensions={...})` - Transpose tensor
- `concatenate(A)` - Concatenate tensors
- `slice(A, slice={...})` - Extract slice
- `dynamic_update_slice(A, B, dims)` - Update slice

**Data Type Operations:**

- `convert(A)` - Convert data type
- `bitcast_convert(A)` - Bitcast conversion

**Linear Algebra:**

- `dot(A, B, lhs_batch_dims={...}, lhs_contracting_dims={...}, rhs_batch_dims={...}, rhs_contracting_dims={...})` - Matrix multiplication

**Broadcast & Constants:**

- `broadcast(A)` - Broadcast tensor
- `broadcast_type(A)` - Type-aware broadcast
- `constant(value)` - Create constant tensor

**Reduction:**

- `reduce(A, B, dims, operation)` - Reduce along dimensions. Right now,
  the only options for `operation` are `add_f32`, `max_f32`. (ADD MORE)

**Conditionals:**

- `select_lt(A, B, C, D)` - Select based on less-than comparison
- `clamp(min, A, max)` - Clamp values to range

### Control Flow

**Conditionals:**

```
IF(condition)
{
    // statements
}
```

**Loops\*:**

```
REPEAT(variable, range)
{
    // statements using @l.variable
}
```

\* While REPEAT blocks are supported, it is _highly_ recommended for speed of compilation that you modify your tensor shapes and operations so a REPEAT is not necessary. We have an example of this in `TAIDL_amx.py` where we have two versions of the instruction `tdpbusd`, one with and without REPEAT.
