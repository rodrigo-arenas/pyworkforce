from pyworkforce.utils import ParameterGrid
from collections.abc import Iterable, Sized
from itertools import chain, product
import pytest


def assert_grid_iter_equals_getitem(grid):
    assert list(grid) == [grid[i] for i in range(len(grid))]


def test_parameter_grid():
    """
    Test taken from scikit-learn
    """
    # Test basic properties of ParameterGrid.
    params1 = {"foo": [1, 2, 3]}
    grid1 = ParameterGrid(params1)
    assert isinstance(grid1, Iterable)
    assert isinstance(grid1, Sized)
    assert len(grid1) == 3
    assert_grid_iter_equals_getitem(grid1)

    params2 = {"foo": [4, 2],
               "bar": ["ham", "spam", "eggs"]}
    grid2 = ParameterGrid(params2)
    assert len(grid2) == 6

    # loop to assert we can iterate over the grid multiple times
    for i in range(2):
        # tuple + chain transforms {"a": 1, "b": 2} to ("a", 1, "b", 2)
        points = set(tuple(chain(*(sorted(p.items())))) for p in grid2)
        assert (points ==
                set(("bar", x, "foo", y)
                    for x, y in product(params2["bar"], params2["foo"])))
    assert_grid_iter_equals_getitem(grid2)

    # Special case: empty grid (useful to get default estimator settings)
    empty = ParameterGrid({})
    assert len(empty) == 1
    assert list(empty) == [{}]
    assert_grid_iter_equals_getitem(empty)
    with pytest.raises(IndexError):
        empty[1]

    has_empty = ParameterGrid([{'C': [1, 10]}, {}, {'C': [.5]}])
    assert len(has_empty) == 4
    assert list(has_empty) == [{'C': 1}, {'C': 10}, {}, {'C': .5}]
    assert_grid_iter_equals_getitem(has_empty)


def test_non_iterable_parameter_grid():
    params = {"foo": 4,
              "bar": ["ham", "spam", "eggs"]}
    with pytest.raises(Exception) as excinfo:
        grid = ParameterGrid(params)
        for grid in params:
            for key in grid:
                assert str(excinfo.value) == 'Parameter grid value is not iterable '
                '(key={!r}, value={!r})'.format(key, grid[key])


def test_non_dict_parameter_grid():
    params = [4]
    with pytest.raises(Exception) as excinfo:
        grid = ParameterGrid(params)
        for grid in params:
            assert str(excinfo.value) == 'Parameter grid is not a dict ({!r})'.format(grid)


def test_wrong_parameter_grid():
    params = 4
    with pytest.raises(Exception) as excinfo:
        grid = ParameterGrid(params)
        for grid in params:
            assert str(excinfo.value) == 'Parameter grid is not a dict or a list ({!r})'.format(params)
