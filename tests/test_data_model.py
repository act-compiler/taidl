import pytest

from taidl import Accelerator
from taidl.data_model import TYPES


class TestTypes:
    @pytest.mark.parametrize('typ', TYPES)
    def test_type_accepted(self, typ):
        acc = Accelerator('Model', base_dir='.')
        acc.add_data_model('d1', [4], [4], typ)
        assert acc.data_model[1].var_type == typ

    @pytest.mark.parametrize('typ', ['float32', 'c64', 'S8', ''])
    def test_type_refused(self, typ):
        acc = Accelerator('Model', base_dir='.')
        with pytest.raises(ValueError, match=f"d1: type '{typ}' is not one of pred, s2, s4"):
            acc.add_data_model('d1', [4], [4], typ)
