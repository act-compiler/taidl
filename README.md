# TAIDL: Tensor Accelerator ISA Definition Language

This is a pre-release version of TAIDLv2.  
The latest stable release is TAIDLv1.1.1, which can be found [here](https://github.com/act-compiler/taidl/releases/tag/v1.1.1).

TAIDL is published in [MICRO 2025](https://doi.org/10.1145/3725843.3756075). For detailed evaluations and comparisons, please refer to our [MICRO 2025 Artifact](https://github.com/act-compiler/taidl-artifact-micro25).

This repository contains the source code and documentation for TAIDL, a domain-specific language designed to define instruction set architectures (ISAs) for tensor accelerators. TAIDL aims to provide a flexible and extensible framework for specifying the operations, data types, and memory models of tensor accelerators, facilitating the design and implementation of efficient hardware and software solutions for machine learning workloads.

TAIDL not only standardizes the way tensor accelerator ISAs are specified but also enables automated generation of tools such as test oracles (functional simulators) and compiler backends, significantly reducing the effort required to develop and maintain these components.
The generated test oracles (called TAIDL-TOs) are orders of magnitude faster than existing functional simulators, making them suitable for large-scale testing and validation of tensor accelerator designs.
The generated compiler backends can be easily integrated into existing compiler frameworks, enabling seamless support for custom tensor accelerators in popular machine learning frameworks like JAX and PyTorch.

For more details, refer to the top-level repository of ACT Ecosystem: [act-compiler/act](https://github.com/act-compiler/act).

## Key improvements in TAIDLv2 over v1.1.1

- **Enhanced Language Features**: TAIDLv2 introduces new language constructs and features that improve the user experience and make it easier to define complex ISAs.
- **ANTLR4-based Parser**: TAIDLv2 uses ANTLR4 for parsing, which provides a more robust and flexible parsing mechanism compared to the previous version.
- **More Generators**: TAIDLv2 includes additional tool generators, expanding the range of tools that can be automatically generated from TAIDL specifications (e.g., improved compiler backends, more comprehensive test oracles).
- **Modular Architecture**: The architecture of TAIDL has been redesigned to be more modular, allowing for easier extension and customization of the language and its associated tools.
