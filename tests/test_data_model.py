import re

import pytest

from taidl import Accelerator, DataModel
from taidl.data_model import TYPES


class TestDerivedStrings:
    def test_buffer(self):
        model = DataModel('d1', [128], [64], 'bf16')
        assert model.var_dim == [128, 64]
        assert model.array_dim_str == "['128','64']"
        assert model.num_dim_str == '{1,0}'

    def test_hbm(self):
        d0 = Accelerator('Model', base_dir='.').data_model[0]
        assert (d0.var_name, d0.var_type) == ('d0', 'u8')
        assert d0.var_dim == []
        assert d0.array_dim_str == '[]'
        assert d0.num_dim_str == '{}'


class TestDimensions:
    def test_kept_as_lists_of_its_own(self):
        acc = Accelerator('Model', base_dir='.')
        dimensions, unit_dim = [8], (4,)
        acc.add_data_model('d1', dimensions, unit_dim, 's8')
        dimensions.append(2)
        model = acc.data_model[1]
        assert (model.access_dim, model.unit_dim, model.var_dim) == ([8], [4], [8, 4])
        assert model.array_dim_str == "['8','4']"

    @pytest.mark.parametrize(
        'dimensions, unit_dim', [([128], [64]), ((8, 8), (16, 4)), ([], [16]), ([4], [])]
    )
    def test_positive_integers_accepted(self, dimensions, unit_dim):
        acc = Accelerator('Model', base_dir='.')
        acc.add_data_model('d1', dimensions, unit_dim, 's8')
        model = acc.data_model[1]
        assert (model.access_dim, model.unit_dim) == (list(dimensions), list(unit_dim))

    @pytest.mark.parametrize('what', ['dimensions', 'unit_dim'])
    @pytest.mark.parametrize('given', [[0], [-8], ['8'], [2.5], [True], (8, None), 8, '8'])
    def test_refused(self, what, given):
        sizes = {'dimensions': [4], 'unit_dim': [4], what: given}
        message = f'd1: {what} {given!r} is not a list of positive integers'
        with pytest.raises(ValueError, match=re.escape(message)):
            Accelerator('Model', base_dir='.').add_data_model('d1', var_type='s8', **sizes)


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
