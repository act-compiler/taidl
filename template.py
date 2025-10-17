"""Template processing and code generation utilities

This module provides template loading and string substitution utilities for
TAIDLv2 code generation.
"""

templates = {}
import os

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

def init_templates(filename="templates.txt"):
    # Look for templates.txt in generators/oracle/templates/
    base_dir = os.path.dirname(CUR_DIR)  # Go up to project root
    template_path = os.path.join(base_dir, "generators", "oracle", "templates", filename)
    
    if templates:
        return
    with open(template_path, "r") as file:
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

def indent_code(code: str, level=1):
    indentation = '\t' * level
    return "\n".join(indentation + line if line.strip() else line for line in code.split('\n'))
