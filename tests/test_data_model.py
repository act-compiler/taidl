import pytest

from taidl import Accelerator
from taidl.data_model import TYPES


class TestDimensions:
    def test_kept_as_lists_of_its_own(self):
        acc = Accelerator('Model', base_dir='.')
        dimensions, unit_dim = [8], (4,)
        acc.add_data_model('d1', dimensions, unit_dim, 's8')
        dimensions.append(2)
        model = acc.data_model[1]
        assert (model.access_dim, model.unit_dim, model.var_dim) == ([8], [4], [8, 4])
        assert model.array_dim_str == "['8','4']"


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
