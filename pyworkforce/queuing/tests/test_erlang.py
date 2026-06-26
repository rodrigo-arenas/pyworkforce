import pytest

from pyworkforce.queuing import ErlangC


def test_expected_erlangc_results():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    results = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
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


def test_n_transactions_alias():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    assert erlang.n_transactions == 100
    assert erlang.n_transactions == erlang.transactions


def test_scale_positions_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    results = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
    positions = results['positions']
    service_level = erlang.service_level(positions=positions, scale_positions=True)
    occupancy = erlang.achieved_occupancy(positions=positions, scale_positions=True)
    waiting_probability = erlang.waiting_probability(positions=positions, scale_positions=True)

    assert positions == 20
    assert round(service_level, 3) == 0.888
    assert round(occupancy, 3) == 0.714
    assert round(waiting_probability, 3) == 0.174


def test_over_occupancy_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    results = erlang.required_positions(service_level=0.8, max_occupancy=0.7)
    raw_positions = results['raw_positions']
    positions = results['positions']
    service_level = erlang.service_level(positions=positions, scale_positions=True)
    occupancy = erlang.achieved_occupancy(positions=positions, scale_positions=True)
    waiting_probability = erlang.waiting_probability(positions=positions, scale_positions=True)

    assert raw_positions == 15
    assert positions == 22
    assert round(service_level, 3) == 0.941
    assert round(occupancy, 3) == 0.667
    assert round(waiting_probability, 3) == 0.102


def test_wrong_transactions_erlangc():
    with pytest.raises(ValueError) as excinfo:
        erlang = ErlangC(transactions=-20, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    assert "transactions must be a positive number" in str(excinfo.value)


def test_wrong_aht_erlangc():
    with pytest.raises(ValueError) as excinfo:
        erlang = ErlangC(transactions=100, asa=0.33, aht=-5, interval=30, shrinkage=0.3)
    assert "aht must be a positive number" in str(excinfo.value)


def test_wrong_asa_erlangc():
    with pytest.raises(ValueError) as excinfo:
        erlang = ErlangC(transactions=100, asa=0, aht=5, interval=30, shrinkage=0.3)
    assert "asa must be a positive number" in str(excinfo.value)


def test_wrong_interval_erlangc():
    with pytest.raises(ValueError) as excinfo:
        erlang = ErlangC(transactions=100, asa=10, aht=5, interval=-30, shrinkage=0.3)
    assert "interval must be a positive number" in str(excinfo.value)


def test_wrong_shrinkage_erlangc():
    with pytest.raises(ValueError) as excinfo:
        erlang = ErlangC(transactions=100, asa=10, aht=5, interval=30, shrinkage=1)
    assert "shrinkage must be in the interval [0, 1)" in str(excinfo.value)


def test_wrong_service_level_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(ValueError) as excinfo:
        results = erlang.required_positions(service_level=1.8, max_occupancy=0.85)
    assert "service_level must be in the interval [0, 1]" in str(excinfo.value)


def test_wrong_max_occupancy_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(ValueError) as excinfo:
        results = erlang.required_positions(service_level=0.8, max_occupancy=1.2)
    assert "max_occupancy must be in the interval (0, 1]" in str(excinfo.value)


def test_zero_max_occupancy_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(ValueError) as excinfo:
        erlang.required_positions(service_level=0.8, max_occupancy=0)
    assert "max_occupancy must be in the interval (0, 1]" in str(excinfo.value)


def test_waiting_probability_requires_productive_positions():
    erlang = ErlangC(transactions=1, asa=0.33, aht=1, interval=30, shrinkage=0.9)
    with pytest.raises(Exception) as excinfo:
        erlang.waiting_probability(positions=1, scale_positions=True)
    assert str(excinfo.value) == "productive positions must be greater than 0"


def test_erlang_methods_require_stable_system():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.0)

    with pytest.raises(Exception) as excinfo:
        erlang.waiting_probability(positions=10)
    assert str(excinfo.value) == "positions must be greater than traffic intensity"

    with pytest.raises(Exception) as excinfo:
        erlang.service_level(positions=10)
    assert str(excinfo.value) == "positions must be greater than traffic intensity"

    with pytest.raises(Exception) as excinfo:
        erlang.achieved_occupancy(positions=10)
    assert str(excinfo.value) == "positions must be greater than traffic intensity"
