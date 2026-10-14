from dataclasses import dataclass

# The element types, as the grammar's TYPE rule lexes them
TYPES = (
    'pred',
    's2',
    's4',
    's8',
    's16',
    's32',
    's64',
    'u2',
    'u4',
    'u8',
    'u16',
    'u32',
    'u64',
    'f8e4m3fn',
    'f8e5m2',
    'f16',
    'bf16',
    'f32',
    'f64',
)


@dataclass
class State:
    name: str
    value: int


class DataModel:
    var_name: str
    var_dim: list[int]
    access_dim: list[int]
    unit_dim: list[int]
    var_type: str
    array_dim_str: str
    num_dim_str: str

    def __init__(self, var_name: str, access_dim: list[int], unit_dim: list[int], var_type: str):
        self.var_name = var_name
        # Lists of its own, whatever sequence it is given
        self.access_dim = list(access_dim)
        self.unit_dim = list(unit_dim)
        self.var_dim = self.access_dim + self.unit_dim
        self.var_type = var_type
        self.array_dim_str = self.create_arr_str(self.var_dim)
        self.num_dim_str = self.create_num_str()

    def create_arr_str(self, dims: list[int]) -> str:
        return '[' + ','.join(f"'{dim}'" for dim in dims) + ']'

    def create_num_str(self) -> str:
        output = '{'
        for i in range(len(self.var_dim) - 1, -1, -1):
            if i == 0:
                output += str(i)
            else:
                output += str(i) + ','
        output += '}'
        return output
