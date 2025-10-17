import os
import re

templates = {}

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

function_templates = {
    "RESHAPE": r'reshape\(%(?P<in>.*?)\);$',
    "SIGN": r'sign\(%(?P<in>.*?)\);$',
    "CONVERT": r'convert\(%(?P<in>.*?)\);$',
    "CONCATENATE": r'concatenate\(%(?P<in>.*?)\);$',
    "BITCAST_CONVERT": r'bitcast_convert\(%(?P<in>.*?)\);$',
    "TRANSPOSE": r'transpose\(%(?P<in>.*?)\),dimensions={(?P<dims>.*?)};$',
    "DOT": r'dot\(%(?P<A>.*?),%(?P<B>.*?)\),lhs_batch_dims={(?P<lb>.*?)},lhs_contracting_dims={(?P<lc>.*?)},rhs_batch_dims={(?P<rb>.*?)},rhs_contracting_dims={(?P<rc>.*?)};$',
    "SLICE": r'slice\(%(?P<in>.*?)\),slice={(?P<dims>.*?)};$',
    "DYNAMIC_UPDATE_SLICE": r'dynamic_update_slice\(%(?P<A>.*?),%(?P<B>.*?),(?P<dims>.*?)\);$',
    "CONSTANT": r'constant\((?P<const>.*?)\);$',
    "BROADCAST": r'broadcast\(%(?P<A>.*?)\);$',
    "BROADCAST_DIM": r'broadcast_dim\(%(?P<A>.*?), (?P<dims>.*?)\);$',
    "BROADCAST_TYPE": r'broadcast_type\(%(?P<A>.*?)\);$',
    "MAXIMUM": r'maximum\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "CLAMP": r'clamp\((?P<A>.*?),%(?P<B>.*?),(?P<C>.*?)\);$',
    "MINIMUM": r'minimum\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "SELECT_LT": r'select_lt\(%(?P<A>.*?),%(?P<B>.*?),%(?P<C>.*?),%(?P<D>.*?)\);$',
    "XOR": r'xor\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "ADD": r'add\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "EXP": r'exp\(%(?P<in>.*?)\);$',
    "TANH": r'tanh\(%(?P<in>.*?)\);$',
    "SQRT": r'sqrt\(%(?P<in>.*?)\);$',
    "RSQRT": r'rsqrt\(%(?P<in>.*?)\);$',
    "SUBTRACT": r'subtract\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "MULTIPLY": r'multiply\(%(?P<A>.*?),%(?P<B>.*?)\);$',
    "REDUCE": r'reduce\(%(?P<A>.*?),%(?P<B>.*?),(?P<dims>.*?),(?P<to_apply>.*?)\);$',
    "DIVIDE": r'divide\(%(?P<A>.*?),%(?P<B>.*?)\);$',
}

statement_templates = {
    "IF": r'IF\((?P<config>.*?)\)$',
    "ELSE": r'ELSE$',
    "REPEAT": r'REPEAT\((?P<loop_var>.*?), (?P<loop_range>.*?)\)$'
}

line_pattern = r'%(?P<lhs>.*?):(?P<dim>.*?)(?P<operation>(<-|=|->))(?P<rhs>.*)$'


def init_templates(filename="templates.txt"):
    global templates
    filename = os.path.join(CUR_DIR, filename)
    if templates:
        return
    with open(filename, "r") as file:
        content = file.read()
    for section in content.split("### TEMPLATE: "):
        if section.strip():
            header, body = section.split(" ###\n", 1)
            body = body.replace('tab ', '\t')
            templates[header.strip()] = body


def generate_code(template: str, inputs):
    temp = template
    for key, value in inputs.items():
        temp = temp.replace(f"{{{{{key}}}}}", value)
    return temp


def write_file(code: str, filename: str):
    with open(filename, "w") as file:
        file.write(code)
    # print(f"Wrote {filename}")


def indent_code(code: str, level=1):
    indentation = '\t' * level
    return "\n".join(indentation + line if line.strip() else line for line in code.split('\n'))


def get_size_str(input_string):
    enclosed_substrings = re.findall(r'`[^`]*`', input_string)
    temp_string = input_string
    for i, substring in enumerate(enclosed_substrings):
        temp_string = temp_string.replace(substring, f"__{i}__", 1)
    parts = temp_string.split('x')
    result = []
    for part in parts:
        for i, substring in enumerate(enclosed_substrings):
            part = (part.replace(f"__{i}__", substring)).replace("`", "")
        result.append(part)

    output = "["
    for part in result:
        output += "'" + part + "',"
    output += "]"
    return output


def map_pattern(pattern, line):
    pattern = re.compile(pattern, re.VERBOSE)
    match = re.match(pattern, line)
    if (not match):
        raise SyntaxError(line)
    mapping = match.groupdict()
    return mapping


def format_input(input):
    return input.strip().replace(" ", "").split("\n")


def var_to_string(var):
    return "'" + var.strip() + "'"


def func_name(rhs):
    name = rhs.strip().split("(")[0].upper()
    if (name not in function_templates):
        print(name)
        raise SyntaxError("Function not found")
    return name


def lhs_map(mapping):
    dim = mapping["dim"].rsplit("x", 1)
    name = var_to_string(mapping["lhs"])
    if (len(dim) == 1):
        return name, "[]", var_to_string(dim[0])
    size = get_size_str(dim[0])
    type = var_to_string(dim[1])
    return name, size, type


def rhs_map(mapping):
    rhs = mapping["rhs"].split("[")
    name = var_to_string(rhs[0])
    bracket = rhs[1].split("]")[0].replace("`", "")
    slice = "['" + bracket.replace(",", "','") + "']"
    return name, slice


def parse_line(line):
    mapping = map_pattern(line_pattern, line)
    mapping["STATEMENT"] = "STATEMENT"

    line_map = {}
    line_map["lhs"], line_map["size"], line_map["type"] = lhs_map(mapping)

    if mapping["operation"] == "<-":
        line_map["STATEMENT"] = "SLICE_LOAD"
        line_map["rhs_name"], line_map["slice"] = rhs_map(mapping)

    elif mapping["operation"] == "->":
        line_map["STATEMENT"] = "SLICE_STORE"
        line_map["rhs_name"], line_map["slice"] = rhs_map(mapping)

    elif mapping["operation"] == "=":
        line_map["STATEMENT"] = "ASSIGNMENT"
        func = func_name(mapping["rhs"])
        line_map["func_name"] = func
        new_map = map_pattern(function_templates[func], mapping["rhs"])
        for key, value in new_map.items():
            line_map[key] = var_to_string(value)
    else:
        raise SyntaxError("Operation not found")

    return line_map


def statement_key(line):
    key = None
    for k, v in statement_templates.items():
        if (line.startswith(k)):
            key = k
            break
    return key


def parse_input(input_str):
    lines = format_input(input_str)
    data, index = parse_block(lines)
    return data


def parse_block(lines, i=0, root=True):
    parsed_data = []
    open_braces = 0

    while i < len(lines):
        line = (lines[i])
        key = statement_key(line)

        if line == "{" and not root:
            open_braces += 1
            i += 1
        elif line == "}" and not root:
            open_braces -= 1
            i += 1
            if open_braces == 0:
                break
        elif (key is not None):
            mapping = map_pattern(statement_templates[key], line)
            config = {}
            config["config"] = ""
            config["loop_var"] = ""
            config["loop_range"] = ""
            if ("config" in mapping):
                config["config"] = (mapping["config"])
            if ("loop_var" in mapping):
                config["loop_var"] = (mapping["loop_var"])
            if ("loop_range" in mapping):
                config["loop_range"] = (mapping["loop_range"])
            i += 1
            block, i = parse_block(lines, i, False)
            parsed_data.append({
                "STATEMENT": key,
                "CONFIG": config,
                "BODY": block
            })
        else:
            if (line):
                parsed_line = parse_line(line)
                parsed_data.append(parsed_line)
            i += 1

    return parsed_data, i
