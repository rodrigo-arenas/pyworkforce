import pytest
from pyworkforce.queuing.erlang import ErlangC


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


def test_wrong_service_level_erlangc():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(Exception) as excinfo:
        results = erlang.required_positions(service_level=1.8, max_occupancy=0.85)
    assert str(excinfo.value) == "service_level must be between 0 and 1"
