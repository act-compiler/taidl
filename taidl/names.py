"""The rule for every name a spec gives"""

import keyword
from collections.abc import Iterable


def check_name(kind: str, name: str, taken: Iterable[str] = ()) -> None:
    """Refuse a name that is not an ASCII identifier, is a Python keyword, or is taken."""
    if not (isinstance(name, str) and name.isascii() and name.isidentifier()):
        raise ValueError(f'{kind} name {name!r} is not an identifier')
    if keyword.iskeyword(name):
        raise ValueError(f"{kind} name '{name}' is a Python keyword")
    if name in taken:
        raise ValueError(f"{kind} name '{name}' is given twice")
