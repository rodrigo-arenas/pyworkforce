import pytest
from pyworkforce.shifts.utils import check_positive_integer, check_positive_float


def test_check_positive_integer():
    assert check_positive_integer('my_val', 5)


def test_check_non_positive_integers():
    with pytest.raises(Exception) as excinfo:
        result = check_positive_integer('my_val', -1)
        assert str(excinfo.value) == "my_val must be a positive integer"

    with pytest.raises(Exception) as excinfo:
        result = check_positive_integer('my_val2', 5.4)
        assert str(excinfo.value) == "my_val2 must be a positive integer"


def test_check_positive_float():
    assert check_positive_float('my_val', 2.43)


def test_check_non_positive_floats():
    with pytest.raises(Exception) as excinfo:
        result = check_positive_float('my_val', -45.3)
        assert str(excinfo.value) == "my_val must be a positive float"

    with pytest.raises(Exception) as excinfo:
        result = check_positive_float('my_val2', 80)
        assert str(excinfo.value) == "my_val2 must be a positive float"
