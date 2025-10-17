import re


def generate_loop_eqs_from_expression(expression):
    expr = expression.replace(' ', '')
    pattern = r'([+-]?\d+)\*\%([a-zA-Z]\w*(?:\.[a-zA-Z0-9]+)?)'
    # pattern = r'([+-]?\d+)\*\%([a-zA-Z]\w*)'
    matches = re.findall(pattern, expr)
    result = []
    for const, var in matches:
        result.append((int(const), var))
    cleaned_expr = re.sub(pattern, '', expr)
    leftovers = re.findall(r'([+-]?\d+)', cleaned_expr)
    for const in leftovers:
        result.append((int(const), None))
    return result


def generate_loop_eq_vars(expression, global_counters):
    eqs = generate_loop_eqs_from_expression(expression)
    additions = []
    op_counter = 0
    hlo_lines = ""
    for (a, b) in eqs:
        if (b is None):
            hlo_lines += f"%loop_int.{global_counters['loop_var']}.{op_counter} = s32[] constant({a})\n"
        else:
            hlo_lines += f"%loop_int.{global_counters['loop_var']}.{op_counter} = s32[] multiply(s32[] constant({a}), %{b})\n"
        additions.append(f"%loop_int.{global_counters['loop_var']}.{op_counter}")
        op_counter += 1

    for idx, add_param in enumerate(additions):
        if (idx == 0):
            cur = add_param
            continue
        op_counter += 1
        if (idx == len(additions) - 1):
            hlo_lines += f"%loop_final.{global_counters['loop_var']}.{op_counter} = s32[] add({cur}, {add_param})\n"
            cur = f"%loop_final.{global_counters['loop_var']}.{op_counter}"
        else:
            hlo_lines += f"%loop_int.{global_counters['loop_var']}.{op_counter} = s32[] add({cur}, {add_param})\n"
            cur = f"%loop_int.{global_counters['loop_var']}.{op_counter}"
    return hlo_lines, cur
# print(generate_loop_eq_vars("5 * %io+2*%i+1 + 3 * %h", {'loop_var': 1})[1])
# def generate_loop_eq_vars(expression, global_counters):
    # pattern = r'([+-]?\d*\.?\d+)?\s*\*\s*(%[a-zA-Z_]\w*)\s*([+-]?\s*\d*\.?\d+)?'
    # match = re.match(pattern, expression)

    # if not match:
    # print("Wrong loop format")
    # assert(0)

    # mult_co = eval(match.group(1))
    # var_name = (match.group(2)).strip()
    # add_co = eval(match.group(3))

    # mult_int = f"%mult_intermediate.{global_counters['loop_var']}"

    # hlo_eq_lines = f"""
    # {mult_int} = s32[] multiply(s32[] constant({mult_co}), {var_name})
    # %loop_final.{global_counters['loop_var']}= s32[] multiply(s32[] constant({add_co}), {mult_int})
    # """
    # return hlo_eq_lines, f"%loop_final.{global_counters['loop_var']}"


def replace_values(string, symbol, list):
    pattern = rf'@{symbol}\.(\w+)'
    replaced_string = re.sub(pattern, fr'{list}["\1"]', string)
    return replaced_string


def blind_substitute(template):
    template = replace_values(template, "a", "attrs")
    template = replace_values(template, "s", "state")
    template = replace_values(template, "c", "comp_attrs")
    template = replace_values(template, "l", "lvars")
    return template


def substitute(template, attrs, state, lvars, consts):
    for key, value in attrs.items():
        template = template.replace('@a.' + key, str(value))
    for key, value in state.items():
        template = template.replace('@s.' + key, str(value))
    for key, value in lvars.items():
        template = template.replace('@l.' + key, str(value))
    for key, value in consts.items():
        template = template.replace('@c.' + key, str(value))
    return template


def compute(exp_: str) -> int | float:
    """
    Compute the value of an expression
    """
    import ast

    try:
        if (f"%loop_final" in exp_):
            return exp_
        is_float = False
        if (exp_.startswith("float")):
            is_float = True
            exp_ = exp_[5:]
        output = eval(compile(ast.parse(exp_, mode='eval'), '', 'eval'))
        if (type(output) is float and not is_float):
            output = int(output)
    except Exception:
        print("Expression: ")
        print(exp_)
        output = "Failed"
        assert (0)
    return output


def create_num_str(var_dim: list) -> str:
    output = '{'
    for i in range(len(var_dim) - 1, -1, -1):
        if (i == 0):
            output += str(i)
        else:
            output += str(i) + ","
    output += "}"
    return output


def get_dim(lhs_dim, attrs, state, lvars, consts):
    dim_sizes = simplify_vals(lhs_dim, attrs, state, lvars, consts)
    dim_sizes = ','.join(dim_sizes)
    return "[" + dim_sizes + "]"


def lhs_util(attrs, state, global_counters, lvars, consts, lhs_name, lhs_vartype="", lhs_dim=[]):
    if (lhs_name in global_counters):
        global_counters[lhs_name]["counter"] += 1
        lhs_type = f'{global_counters[lhs_name]["type"]}{global_counters[lhs_name]["dim"]}'
    else:
        num = create_num_str(lhs_dim)
        dim_sizes = simplify_vals(lhs_dim, attrs, state, lvars, consts)
        dim_sizes = ','.join(dim_sizes)
        lhs_type = f'{lhs_vartype}[{dim_sizes}]{num}'
        if (len(dim_sizes) == 0):
            lhs_type = f"{lhs_vartype}[]"
    lhs_name = parameter_util(global_counters, attrs, state, lvars, consts, lhs_name)
    return lhs_name, lhs_type


def parameter_util(global_counters, attrs, state, lvars, consts, lhs_name):
    lhs_name = substitute(lhs_name, attrs, state, lvars, consts)
    if (lhs_name in global_counters):
        lhs_name += f'.{global_counters[lhs_name]["counter"]}'
    else:
        lhs_name += f'.{global_counters["loop_counter"]}'
        lhs_name += f'.{global_counters["instruction_counter"]}'
    lhs_name = "%" + lhs_name
    return lhs_name


def simplify_vals(vals, attrs, state, lvars, consts):
    simplify = lambda x: str((compute(substitute(x, attrs, state, lvars, consts))))
    vals = list(map(simplify, vals))
    return vals


def non_dynamic_slice(slice_configs, attrs, state, lvars, consts):
    slice_configs = [sc.split(':') for sc in slice_configs]
    simplify = lambda x: str(int(compute(substitute(x, attrs, state, lvars, consts))))
    slice_configs = [list(map(simplify, sc)) for sc in slice_configs]
    slice_configs = [('[' + ':'.join(sc) + ']') for sc in slice_configs]
    slice_configs = ', '.join(slice_configs)

    line = f'slice={{{slice_configs}}}'
    return line


def slice_load(lhs, lhs_type, rhs_loc, slice_configs, attrs, state, lvars, consts):
    slice_configs = [sc.split(':') for sc in slice_configs]
    simplify = lambda x: str((compute(substitute(x, attrs, state, lvars, consts))))
    slice_configs = [list(map(simplify, sc)) for sc in slice_configs]
    start_indices = ""
    for sc in slice_configs:
        if ("%" not in sc[0]):
            start_indices += f", s32[] constant({sc[0]})"
        else:
            start_indices += f", {sc[0]}"
    slice_sizes = lhs_type.split('[', 1)[1].split(']')[0]
    line = f'{lhs} = {lhs_type} dynamic-slice({rhs_loc}{start_indices}), '
    line += f'dynamic_slice_sizes={{{slice_sizes}}}'
    return line


def slice_store(
        lhs_loc,
        lhs_type,
        rhs_loc,
        rhs_update,
        start_indices,
        attrs,
        state,
        lvars,
        consts,
        prefix):
    simplify = lambda x: str((compute(substitute(x, attrs, state, lvars, consts))))
    start_indices = list(map(simplify, start_indices))
    lines = []
    # for i in range(len(start_indices)):
    # lines.append(f'%start_indices.{i}.{prefix} = s32[] constant({start_indices[i]})')
    update_slice = f'{lhs_loc} = {lhs_type} dynamic-update-slice({rhs_loc}, {rhs_update}'
    for i in range(len(start_indices)):
        if ("%" not in start_indices[i]):
            update_slice += f', s32[] constant({start_indices[i]})'
        else:
            update_slice += f', {start_indices[i]}'
    update_slice += f')'
    lines.append(update_slice)
    return lines


def reshape_helper(lhs_loc, lhs_type, rhs_loc):
    return f'{lhs_loc} = {lhs_type} reshape({rhs_loc})'


def convert_helper(lhs_loc, lhs_type, rhs_loc):
    return f'{lhs_loc} = {lhs_type} convert({rhs_loc})'


def dot_helper(
        lhs_loc,
        lhs_type,
        rhs_loc_A,
        rhs_loc_B,
        lhs_batch,
        lhs_contracting,
        rhs_batch,
        rhs_contracting):
    line = f'{lhs_loc} = {lhs_type} dot({rhs_loc_A}, {rhs_loc_B}), '
    line += f'lhs_batch_dims={{{lhs_batch}}}, lhs_contracting_dims={{{lhs_contracting}}}, '
    line += f'rhs_batch_dims={{{rhs_batch}}}, rhs_contracting_dims={{{rhs_contracting}}}'
    line += ', operand_precision={HIGHEST}'
    return line
