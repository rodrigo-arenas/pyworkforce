import pytest

from pyworkforce.utils.validation import (
    check_positive_integer,
    check_positive_float,
    check_in_range,
)


def test_check_positive_integer_accepts_positive_int():
    assert check_positive_integer("x", 5) is True


@pytest.mark.parametrize("value", [0, -1, 2.5, "3", None, True, False])
def test_check_positive_integer_rejects_invalid(value):
    with pytest.raises(ValueError):
        check_positive_integer("x", value)


def test_check_positive_float_accepts_int_and_float():
    assert check_positive_float("x", 240) is True
    assert check_positive_float("x", 1.5) is True


@pytest.mark.parametrize("value", [0, -0.1, float("nan"), float("inf"), True, "1"])
def test_check_positive_float_rejects_invalid(value):
    with pytest.raises(ValueError):
        check_positive_float("x", value)


def test_check_in_range_inclusive_bounds():
    assert check_in_range("x", 0, 0, 1) is True
    assert check_in_range("x", 1, 0, 1) is True


def test_check_in_range_exclusive_bounds():
    assert check_in_range("x", 0.5, 0, 1, include_low=False, include_high=False) is True
    with pytest.raises(ValueError):
        check_in_range("x", 1, 0, 1, include_high=False)
    with pytest.raises(ValueError):
        check_in_range("x", 0, 0, 1, include_low=False)


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), True])
def test_check_in_range_rejects_invalid(value):
    with pytest.raises(ValueError):
        check_in_range("x", value, 0, 1)


def test_error_message_includes_parameter_name():
    with pytest.raises(ValueError) as excinfo:
        check_positive_integer("num_days", -1)
    assert "num_days" in str(excinfo.value)
