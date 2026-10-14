# Semantics

`add_semantics(semantics)` takes one `ENTRY` block, written in a dialect of XLA-HLO text, and parses it at once; a second call replaces the first.

```
ENTRY {
    // <comment>
    %In0 = <type>[<shape>] parameter(0);
    %<value> = <type>[<shape>] <operation>(<operands>), <attribute>=<value>;
    ROOT %Out0 = <type>[<shape>] <operation>(<operands>);
}
```

A name is a letter or an underscore followed by letters, digits, underscores and dots.
A value's name follows a `%`, as in `%In0` or `%dot`.
A name with no `%` cannot be a type word, `ENTRY`, `ROOT`, `inf` or `nan`, nor an operation word except where one names an attribute.
The `ENTRY` line carries no name: the block is the semantics of the instruction `add_semantics` is called on.
Each line defines one value: its `%` name, its type and shape, an operation with its operands, then any attributes, each after a comma; the semicolon that ends a line is optional.
Text from `//` to the end of its line is a comment; there is no block comment.
The k-th region of `set_inputs`, counting from 0, enters as `%In<k>`, declared by `parameter(k)` and by no other line; its type is the data model's and its shape is the region's sizes followed by the data model's `unit_dim`.
The k-th region of `set_outputs`, counting from 0, is written from the value named `%Out<k>`.
Exactly one line carries `ROOT`, the mark XLA-HLO text puts on the result of a computation: with one output, the line that defines `%Out0`; with several, each `%Out<k>` has a line of its own and `ROOT` marks the last output, the one of the highest k, wherever its line stands:

```
ENTRY {
    %In0 = f32[8] parameter(0);
    %Out0 = f32[4] slice(%In0), slice={[0:4]};
    ROOT %Out1 = f32[4] slice(%In0), slice={[4:8]};
}
```

Each region has its value and each `%In<k>` and `%Out<k>` its region, checked once the semantics and the regions are both given, in either order: `add_semantics` checks against the regions already set, and `set_inputs` and `set_outputs` against the semantics already added.
An instruction that only changes state has no inputs, no outputs and no semantics: `add_semantics` is not called for it.

## Types and shapes

A type is one of `pred`, `s2`, `s4`, `s8`, `s16`, `s32`, `s64`, `u2`, `u4`, `u8`, `u16`, `u32`, `u64`, `f8e4m3fn`, `f8e5m2`, `f16`, `bf16`, `f32` and `f64`, as XLA-HLO text spells them: the boolean, the signed and unsigned integers by width, and the floats by width.
`f8e4m3fn` and `f8e5m2` are the two common 8-bit floats, named by their exponent and mantissa bits.
XLA-HLO's other element types stay out: the complex types, since no operation on complex numbers is lexed, and the rarer formats, which are the one-bit integers, the other 8-bit floats and the 4- and 6-bit floats.
A quantized type, which carries a scale and a zero point beside its storage type, is a different kind of type and would need syntax the grammar lacks.
A shape lists the dimensions between the brackets, each an integer or an expression in backticks; `f32[]` is a rank-0 value.

## Operands and attributes

An operand is a value by its `%` name, which an earlier line defines, and no two lines define one name.
Two words take something else: `parameter` takes the number of an input, and `constant` takes one literal, a number such as `7`, `-128`, `0.5`, `1e-3`, `inf`, `-inf` or `nan`, `true`, `false` or an expression in backticks.
An attribute is named as XLA-HLO text names it, by a name with no `%`, and its value takes one of three forms:

| form       | example                             |
| ---------- | ----------------------------------- |
| value      | `direction=LT`                      |
| brace list | `dimensions={1,0}`, `dimensions={}` |
| slice list | `slice={[0:4:2], [1:2]}`            |

A value is a number, a name with no `%` such as `LT` or `true`, or an expression in backticks, and a brace list holds any number of them.
A slice list holds one or more ranges, each `[start:limit]` or `[start:limit:stride]`.
XLA-HLO text writes the attribute of `pad` as `padding=0_1x2_3`, which is none of the three forms; a semantics gives `pad` StableHLO's three attributes instead, `edge_padding_low`, `edge_padding_high` and `interior_padding`, each a brace list.

## What is refused

`add_semantics` raises `SyntaxError` for text the grammar does not accept, naming the instruction and the line and column of the first error.
That covers a character no token holds, such as `$`, an `@` outside backticks or a sign with no digits after it; a type or an operation outside those listed above and in `operations.md`, such as `c64` or the hyphenated `log-plus-one`; a dimension that is neither an integer nor an expression in backticks; an empty text or a block with no line; and text after the closing brace.
It raises `SyntaxError` too for a name between `ENTRY` and its brace, for a line whose name has no `%`, for a line whose operands or attributes break its word's row, for an operand no earlier line defines and a name two lines define, for a `parameter(k)` that declares a name other than `%In<k>` and an `%In<k>` that another operation declares, for a block that carries no `ROOT` or several, and for a `ROOT` on any line but the last output's.
`add_semantics`, `set_inputs` and `set_outputs` raise `SyntaxError` for a region without its value and for a value without its region.
The calls that take an expression raise `SyntaxError` for one the expression grammar does not accept or that refers to a name not declared, naming the instruction, the place and the line and column there: `add_semantics` names the semantics, `set_inputs` and `set_outputs` the start or the size, and `add_instruction` and `add_constraints` the constraint or the update, each quoted but the semantics.
TAIDL checks the form of a semantics, not its meaning: whether the shapes and element types agree and whether an operation is supported are for each generator to check.
