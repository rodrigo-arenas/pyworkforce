import pytest

from pyworkforce.queuing.erlang import MultiErlangC


def test_expected_multierlangc_results():
    param_grid = {"transactions": [100], "asa": [0.33], "aht": [3], "interval": [30], "shrinkage": [0.3]}
    erlang = MultiErlangC(param_grid=param_grid)
    arguments_grid = {"service_level": [0.8], "max_occupancy": [0.85]}
    results = erlang.required_positions(arguments_grid=arguments_grid)[0]
    raw_positions = results['raw_positions']
    positions = results['positions']
    service_level = results['service_level']
    occupancy = results['occupancy']
    waiting_probability = results['waiting_probability']

    assert raw_positions == 14
    assert positions == 20
    assert round(service_level, 3) == 0.888
    assert round(occupancy, 3) == 0.714
    assert round(waiting_probability, 3) == 0.174


def test_expected_multierlangc_grid():
    param_grid = {"transactions": [100], "asa": [0.33], "aht": [3], "interval": [30], "shrinkage": [0.3]}
    erlang = MultiErlangC(param_grid=param_grid)
    arguments_grid = {"service_level": [0.8, 0.9], "max_occupancy": [0.85]}
    results_list = erlang.required_positions(arguments_grid=arguments_grid)

    assert len(results_list) == 2

    results = results_list[0]

    raw_positions = results['raw_positions']
    positions = results['positions']
    service_level = results['service_level']
    occupancy = results['occupancy']
    waiting_probability = results['waiting_probability']

    assert raw_positions == 14
    assert positions == 20
    assert round(service_level, 3) == 0.888
    assert round(occupancy, 3) == 0.714
    assert round(waiting_probability, 3) == 0.174

    results = results_list[1]

    raw_positions = results['raw_positions']
    positions = results['positions']
    service_level = results['service_level']
    occupancy = results['occupancy']
    waiting_probability = results['waiting_probability']

    assert raw_positions == 15
    assert positions == 22
    assert round(service_level, 3) == 0.941
    assert round(occupancy, 3) == 0.667
    assert round(waiting_probability, 3) == 0.102


def test_multiscale_positions_erlangc():
    param_grid = {"transactions": [100], "asa": [0.33], "aht": [3], "interval": [30], "shrinkage": [0.3]}
    erlang = MultiErlangC(param_grid=param_grid)
    arguments_grid = {"service_level": [0.8], "max_occupancy": [0.85]}
    results = erlang.required_positions(arguments_grid=arguments_grid)[0]
    positions = results['positions']

    arguments_grid = {"positions": [positions], "scale_positions": [True]}
    service_level = erlang.service_level(arguments_grid)[0]
    occupancy = erlang.achieved_occupancy(arguments_grid)[0]
    waiting_probability = erlang.waiting_probability(arguments_grid)[0]

    assert positions == 20
    assert round(service_level, 3) == 0.888
    assert round(occupancy, 3) == 0.714
    assert round(waiting_probability, 3) == 0.174


def test_expected_multierlangc_wrong_arguments():
    param_grid = {"transactions": [100], "asa": [0.33], "aht": [3], "interval": [30], "shrinkage": [0.3]}
    erlang = MultiErlangC(param_grid=param_grid)
    arguments_grid = {"max_occupancy": [0.85]}

    with pytest.raises(Exception) as excinfo:
        results = erlang.required_positions(arguments_grid=arguments_grid)[0]
    assert str(excinfo.value) in ["required_positions() missing 1 required positional argument: 'service_level'",
                                  "ErlangC.required_positions() missing 1 required positional argument: 'service_level'"]


def test_multierlangc_wrong_grid():
    param_grid = {"transactions": 100, "asa": [0.33], "aht": [3], "interval": [30], "shrinkage": [0.3]}

    with pytest.raises(Exception) as excinfo:
        results = MultiErlangC(param_grid=param_grid)
    assert str(excinfo.value) == "Parameter grid value is not iterable (key='transactions', value=100)"


def test_multierlangc_check_solutions_expected_combinations():
    erlang = MultiErlangC(param_grid={"transactions": [100], "asa": [0.33], "aht": [3], "interval": [30]})

    with pytest.raises(Exception) as excinfo:
        erlang._check_solutions([{}], combinations=2)
    assert str(excinfo.value) == "Inconsistent results. Expected 2 solutions, got 1"


def test_multierlangc_records_params_for_every_method():
    """Regression test: every method must populate its *_params attribute."""
    param_grid = {"transactions": [100, 120], "asa": [0.33], "aht": [3],
                  "interval": [30], "shrinkage": [0.3]}
    erlang = MultiErlangC(param_grid=param_grid, n_jobs=1)

    positions_grid = {"positions": [20, 25]}
    erlang.waiting_probability(positions_grid)
    erlang.service_level(positions_grid)
    erlang.achieved_occupancy(positions_grid)
    erlang.required_positions({"service_level": [0.8], "max_occupancy": [0.85]})

    # 2 transaction values * 2 position values = 4 combinations.
    assert len(erlang.waiting_probability_params) == 4
    assert len(erlang.service_level_params) == 4
    assert len(erlang.achieved_occupancy_params) == 4
    # 2 transaction values * 1 service-level combination = 2.
    assert len(erlang.required_positions_params) == 2

    # Each entry is a (erlang_params, method_params) tuple.
    erlang_params, method_params = erlang.achieved_occupancy_params[0]
    assert "transactions" in erlang_params
    assert "positions" in method_params


def test_multierlangc_params_align_with_results():
    param_grid = {"transactions": [100, 200], "asa": [0.33], "aht": [3],
                  "interval": [30], "shrinkage": [0.0]}
    erlang = MultiErlangC(param_grid=param_grid, n_jobs=1)
    results = erlang.achieved_occupancy({"positions": [30]})

    assert len(results) == len(erlang.achieved_occupancy_params)
    # Higher transaction volume -> higher occupancy for the same positions.
    occ_by_transactions = {
        params[0]["transactions"]: occ
        for params, occ in zip(erlang.achieved_occupancy_params, results)
    }
    assert occ_by_transactions[200] > occ_by_transactions[100]

