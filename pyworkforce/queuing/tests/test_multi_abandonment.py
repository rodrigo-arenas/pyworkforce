import pytest

from pyworkforce.queuing import ErlangA, MultiErlangA

BASE_GRID = {"transactions": [100], "aht": [3], "interval": [30],
             "asa": [20 / 60], "patience": [5], "shrinkage": [0.3]}


def test_multierlanga_matches_single_erlanga():
    multi = MultiErlangA(param_grid=BASE_GRID, n_jobs=1)
    result = multi.required_positions({"service_level": [0.8], "max_occupancy": [0.85],
                                       "max_abandonment": [0.05]})[0]

    single = ErlangA(transactions=100, aht=3, interval=30, asa=20 / 60,
                     patience=5, shrinkage=0.3)
    expected = single.required_positions(service_level=0.8, max_occupancy=0.85,
                                         max_abandonment=0.05)
    assert result == expected


def test_multierlanga_grid_expands():
    grid = {"transactions": [100, 120], "aht": [3], "interval": [30],
            "asa": [20 / 60], "patience": [5], "shrinkage": [0.0]}
    multi = MultiErlangA(param_grid=grid, n_jobs=1)
    results = multi.required_positions({"service_level": [0.8, 0.9]})
    assert len(results) == 4
    assert len(multi.required_positions_params) == 4


def test_multierlanga_records_params_for_every_method():
    multi = MultiErlangA(param_grid=BASE_GRID, n_jobs=1)
    positions_grid = {"positions": [14, 16]}

    multi.waiting_probability(positions_grid)
    multi.abandonment_probability(positions_grid)
    multi.achieved_occupancy(positions_grid)
    multi.average_speed_of_answer(positions_grid)
    multi.average_queue_length(positions_grid)
    multi.service_level(positions_grid)
    multi.required_positions({"service_level": [0.8]})

    assert len(multi.waiting_probability_params) == 2
    assert len(multi.abandonment_probability_params) == 2
    assert len(multi.achieved_occupancy_params) == 2
    assert len(multi.average_speed_of_answer_params) == 2
    assert len(multi.average_queue_length_params) == 2
    assert len(multi.service_level_params) == 2
    assert len(multi.required_positions_params) == 1


def test_multierlanga_scalar_methods_return_floats():
    multi = MultiErlangA(param_grid=BASE_GRID, n_jobs=1)
    waits = multi.waiting_probability({"positions": [14, 16]})
    assert len(waits) == 2
    assert all(0 <= w <= 1 for w in waits)
    # More positions -> lower waiting probability.
    assert waits[1] < waits[0]


def test_multierlanga_wrong_grid_raises():
    with pytest.raises(Exception) as excinfo:
        MultiErlangA(param_grid={"transactions": 100, "aht": [3]})
    assert "not iterable" in str(excinfo.value)


def test_multierlanga_check_solutions_inconsistent():
    multi = MultiErlangA(param_grid=BASE_GRID, n_jobs=1)
    with pytest.raises(ValueError) as excinfo:
        multi._check_solutions([{}], combinations=2)
    assert "Inconsistent results" in str(excinfo.value)


def test_multierlanga_check_solutions_empty():
    multi = MultiErlangA(param_grid=BASE_GRID, n_jobs=1)
    with pytest.raises(ValueError) as excinfo:
        multi._check_solutions([], combinations=0)
    assert "Could not find any solution" in str(excinfo.value)


def test_multierlanga_repr():
    multi = MultiErlangA(param_grid=BASE_GRID)
    assert repr(multi).startswith("MultiErlangA(")
