# Instructions

`add_instruction(name, computation_attr, addressing_attr, *, update=(), constraints=())` declares an instruction and returns it; `update` and `constraints` are passed by keyword.
Each of the four is a list of strings, and one string in place of a list raises `TypeError`.
`add_constraints(constraints)` takes a list of constraints and appends them to those the instruction already has.
`set_inplace(inplace)` marks the inputs an instruction overwrites, one flag per input, after `set_inputs`, which resets every mark to False.
`set_apart(apart)` and `set_no_partial_overlap(no_partial)` take one flag per input of an instruction with exactly one output; each marked input shares the output's buffer and is not marked in place.
`set_apart` appends one constraint per marked input: the output lies apart from it along at least one addressed dimension whose starts are spelled differently; an input whose starts are all spelled as the output's cannot be marked.
`set_no_partial_overlap` appends one constraint per marked input and per addressed dimension whose starts are spelled differently: the starts there are equal, or the output lies apart from it.
Starts are compared as parsed, so spacing never makes two differ.
Each of the two, given again, replaces the constraints it appended before.
`add_initial_state(name, value)` declares a machine state variable with its initial value, an integer, any other value raising `ValueError`; an expression reads it as `@s.<name>`, and an instruction's `update` lines say how it changes, as in `@s.<name> = 1`.
