# Declarations

`Accelerator(name, base_dir=None)` starts with one data model, `d0`, the off-chip memory: a flat buffer of `u8` bytes.
`add_data_model(name, dimensions, unit_dim, var_type)` declares an on-chip buffer: `dimensions` are the dimensions an instruction addresses, `unit_dim` is the shape of one addressed unit, each a list of positive integers, and `var_type` is the element type, one of the types a semantics may write.
An instruction has computational attributes, which configure what it computes, and addressing attributes, which say where its operands lie.
`set_inputs(inputs)` and `set_outputs(outputs)` each take a list of regions `[buffer, starts, sizes]`: the name of a data model, then one start and one size per addressed dimension, so a buffer declared with no addressed dimension takes none.
`d0` is the exception: it has no addressed dimension and takes one start and one size, in bytes.
A start is an integer or an expression, which refers to a computational attribute as `@c.<name>`, to an addressing attribute as `@a.<name>` and to a state variable as `@s.<name>`.
A size is an integer or an expression too, which refers to no addressing attribute.
Every name a spec gives, to the accelerator, a data model, an instruction, an attribute or a state variable, is an identifier: an ASCII letter or an underscore followed by ASCII letters, digits and underscores, and not a Python keyword.
A data model, an instruction and a state variable are each named once, and an attribute once among both attribute lists of its instruction.
A region names a data model the accelerator has declared and gives it as many starts and sizes as it takes.
A dimension, a `var_type`, a name or a region that breaks these rules raises `ValueError`.
A generator takes the accelerator, as in TAIDL-TO's `generate_oracle(acc)` and ACT-Backend's `generate_backend(acc)`, and writes under its `base_dir`, by default the directory of the file that creates the accelerator, or the working directory when no file does.
TAIDL-TO's oracle keeps the names below for itself, and `generate_oracle` refuses a spec that gives one:

| name        | kept by the oracle                                                                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| data model  | `In<k>`, `Out<k>`, `instruction_counter`, `total_loop_counter`, `loop_var`, `loop_final`, `call`, `debug_prefix`, `debug_slice` and `debug_slice_f64`                                             |
| instruction | a name between double underscores, such as `__debug__`, and a name the generated `api.py` keeps, such as `start_loop`, `end_loop`, `debug` or `str`                                               |
| attribute   | a name between double underscores, `comp_attrs`, `cur_scope`, `global_counters`, `instruction_scopes`, `ssa_types`, `state`, and a name its instruction's generated function reads, such as `str` |
| value       | `%` and a data model's name, or `%instruction_counter`, `%total_loop_counter`, `%loop_var` or `%loop_final`                                                                                       |
