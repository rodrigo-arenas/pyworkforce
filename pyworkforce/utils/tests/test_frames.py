import pytest

from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe


def test_results_to_dataframe_without_params():
    results = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    df = results_to_dataframe(results)
    assert list(df.columns) == ["a", "b"]
    assert df.shape == (2, 2)


def test_results_to_dataframe_scalar_results():
    df = results_to_dataframe([0.8, 0.9])
    assert list(df.columns) == ["result"]
    assert df["result"].tolist() == [0.8, 0.9]


def test_results_to_dataframe_with_params_adds_columns():
    grid = {"transactions": [100], "aht": [3], "interval": [30],
            "asa": [20 / 60], "shrinkage": [0.3]}
    multi = MultiErlangC(param_grid=grid, n_jobs=1)
    results = multi.required_positions({"service_level": [0.8, 0.9], "max_occupancy": [0.85]})
    df = results_to_dataframe(results, multi.required_positions_params)

    assert len(df) == 2
    assert "transactions" in df.columns
    assert "positions" in df.columns


def test_results_to_dataframe_preserves_colliding_keys():
    grid = {"transactions": [100], "aht": [3], "interval": [30],
            "asa": [20 / 60], "shrinkage": [0.3]}
    multi = MultiErlangC(param_grid=grid, n_jobs=1)
    results = multi.required_positions({"service_level": [0.8], "max_occupancy": [0.85]})
    df = results_to_dataframe(results, multi.required_positions_params)

    # Target stays under service_level, achieved goes to service_level_result.
    assert df.loc[0, "service_level"] == 0.8
    assert df.loc[0, "service_level_result"] > 0.8


def test_results_to_dataframe_length_mismatch_raises():
    with pytest.raises(ValueError):
        results_to_dataframe([{"a": 1}], params=[])
