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
    with pytest.raises(Exception) as excinfo:
        erlang = ErlangC(transactions=-20, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    assert str(excinfo.value) == "transactions can't be smaller or equals than 0"


def test_wrong_aht_erlangc():
    with pytest.raises(Exception) as excinfo:
        erlang = ErlangC(transactions=100, asa=0.33, aht=-5, interval=30, shrinkage=0.3)
    assert str(excinfo.value) == "aht can't be smaller or equals than 0"


def test_wrong_asa_erlangc():
    with pytest.raises(Exception) as excinfo:
        erlang = ErlangC(transactions=100, asa=0, aht=5, interval=30, shrinkage=0.3)
    assert str(excinfo.value) == "asa can't be smaller or equals than 0"


def test_wrong_interval_erlangc():
    with pytest.raises(Exception) as excinfo:
        erlang = ErlangC(transactions=100, asa=10, aht=5, interval=-30, shrinkage=0.3)
    assert str(excinfo.value) == "interval can't be smaller or equals than 0"


def test_wrong_shrinkage_erlangc():
    with pytest.raises(Exception) as excinfo:
        erlang = ErlangC(transactions=100, asa=10, aht=5, interval=30, shrinkage=1)
    assert str(excinfo.value) == "shrinkage must be between in the interval [0,1)"


def test_wrong_service_level_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(Exception) as excinfo:
        results = erlang.required_positions(service_level=1.8, max_occupancy=0.85)
    assert str(excinfo.value) == "service_level must be between 0 and 1"


def test_wrong_max_occupancy_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(Exception) as excinfo:
        results = erlang.required_positions(service_level=0.8, max_occupancy=1.2)
    assert str(excinfo.value) == "max_occupancy must be between 0 and 1"
