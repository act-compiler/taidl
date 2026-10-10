"""TAIDL - Tensor Accelerator ISA Definition Language"""

__version__ = '2.10'

from .accelerator import Accelerator
from .instruction import Instruction
from .data_model import DataModel, State

__all__ = ['Accelerator', 'Instruction', 'DataModel', 'State']
