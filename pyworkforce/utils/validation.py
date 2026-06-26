"""Lightweight, dependency-free input validation helpers.

These helpers centralize the parameter checks used across pyworkforce so that
every estimator raises consistent, descriptive error messages. They are kept
intentionally small and free of heavy dependencies so they can be reused from
any module.
"""

from math import isinf, isnan
from numbers import Integral, Real


def check_positive_integer(name, value):
    """Validate that ``value`` is a strictly positive integer.

    Parameters
    ----------
    name : str
        Name of the parameter, used to build the error message.
    value : int
        Value to validate.

    Returns
    -------
    bool
        ``True`` when the value is valid.

    Raises
    ------
    ValueError
        If ``value`` is not a strictly positive integer. Booleans are
        explicitly rejected even though ``bool`` is a subclass of ``int``.
    """
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return True


def check_positive_float(name, value):
    """Validate that ``value`` is a strictly positive, finite number.

    Integers are accepted (e.g. ``max_search_time=240``) and converted by the
    caller as needed. ``NaN`` and infinities are rejected.

    Parameters
    ----------
    name : str
        Name of the parameter, used to build the error message.
    value : float
        Value to validate.

    Returns
    -------
    bool
        ``True`` when the value is valid.

    Raises
    ------
    ValueError
        If ``value`` is not a strictly positive, finite number.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a positive number, got {value!r}")
    if isnan(value) or isinf(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    if value <= 0:
        raise ValueError(f"{name} must be a positive number, got {value!r}")
    return True


def check_in_range(name, value, low, high, include_low=True, include_high=True):
    """Validate that a number lies within a (possibly half-open) interval.

    Parameters
    ----------
    name : str
        Name of the parameter, used to build the error message.
    value : float
        Value to validate.
    low, high : float
        Interval bounds.
    include_low, include_high : bool, default=True
        Whether the bounds are inclusive.

    Returns
    -------
    bool
        ``True`` when the value is within range.

    Raises
    ------
    ValueError
        If ``value`` is not a finite number within the interval.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if isnan(value) or isinf(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")

    low_ok = value >= low if include_low else value > low
    high_ok = value <= high if include_high else value < high
    if not (low_ok and high_ok):
        left = "[" if include_low else "("
        right = "]" if include_high else ")"
        raise ValueError(
            f"{name} must be in the interval {left}{low}, {high}{right}, got {value!r}"
        )
    return True
