# Expressions

An expression is integer arithmetic over attributes and state variables, as in `` `@c.n * 128` `` or `` `@s.dataflow` ``.
It stands in four places: between backticks in a semantics, as a dimension of a shape or as a value; as a start or a size of a region; as a constraint; and as a state update.
It refers to a computational attribute as `@c.<name>`, to an addressing attribute as `@a.<name>` and to a state variable as `@s.<name>`, and a semantics refers to one nowhere else.
Each name it refers to is declared: an attribute by its instruction, and a state variable by `add_initial_state`.
A spec declares its data models and its state, then its instructions: `add_initial_state` after an instruction raises `ValueError`.
A value is built from integers, written in decimal with no sign and no leading zero, and references, with `+`, `-`, `*`, `/`, `%`, a unary `-` and brackets; `*`, `/` and `%` bind tighter than `+` and `-`, and each operator groups from the left.
`/` is floor division, the quotient `floor(a / b)` with no error for an inexact result, so `15 / 2` is 7; `%` is the remainder, with the sign of the divisor.
A start, a size and a backtick expression are values; a constraint is a condition, comparisons of two values by `==`, `!=`, `<`, `<=`, `>` or `>=`, joined by `and` and `or`, `and` binding tighter, with brackets, as in `@a.x + @c.n <= @a.y or @a.y + 64 <= @a.x`.
A state update is `@s.<name> = <value>`, as in `@s.count = (@s.count + 1) % 4`.
There is no `//`, `**`, `not`, function such as `min`, conditional value or chained comparison such as `0 <= @c.n < 8`, and an update has no `+=` or `-=`.
An instruction reads state as it runs: its constraints see the state before it, its updates then run in the order given, and its regions and its semantics' expressions see the state after them.
TAIDL parses each text when the call that takes it runs and keeps its tree beside the text: `instr_expression_asts` maps each backtick expression's node in `instr_semantics_ast` to its tree, `instr_input_asts` and `instr_output_asts` hold each region with a tree per start and per size, and `constraint_asts` and `update_asts` hold one tree per constraint and per update.
