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

def test_required_positions_14():
    erlang = ErlangC(transactions=200, asa=20, aht=3*60, interval=60*60, shrinkage=0.0)
    results = erlang.required_positions(service_level=0.8, max_occupancy=1.0)
    positions = results['positions']

    assert positions == 14


def test_required_positions_81():
    erlang = ErlangC(transactions=202, asa=30, aht=330, interval=15*60, shrinkage=0.0)
    results = erlang.required_positions(service_level=0.8, max_occupancy=1.0)
    positions = results['positions']

    assert positions == 81

def test_what_required_positions():
    erlang = ErlangC(transactions=27, asa=30, aht=233, interval=15*60, shrinkage=0.0)
    results = erlang.required_positions(service_level=0.8, max_occupancy=1.0)
    positions = results['positions']

    print(positions)

    assert positions == 10


def test_what_asa():
    erlang = ErlangC(transactions=27, asa=30, aht=233, interval=15*60, shrinkage=0.0)
    results = erlang.what_asa(positions=4)
    print(results)

    assert results > 0

def test_what_asa_mvp():

    #  {
#     "tc": "2022-12-28 18:15:00+03:00",
#     "call_volume": 231,
#     "aht": 447.4,
#     "service_level": 80,
#     "art": 30,
#     "positions": 124,
#     "scheduled_positions": 81,
#     "scheduled_service_level": 0.0,
#     "scheduled_asa": -163.44
#   },

    erlang = ErlangC(transactions=231, asa=30, aht=447.4, interval=15 * 60, shrinkage=0.0)
    positive_asa = erlang.what_asa(positions=124)
    print(positive_asa)
    assert positive_asa > 0

    scheduled_asa = erlang.what_asa(positions=81)
    print(scheduled_asa)
    assert scheduled_asa > 0

def test_service_level_mvp():

    #  {
#     "tc": "2022-12-28 18:15:00+03:00",
#     "call_volume": 231,
#     "aht": 447.4,
#     "service_level": 80,
#     "art": 30,
#     "positions": 124,
#     "scheduled_positions": 81,
#     "scheduled_service_level": 0.0,
#     "scheduled_asa": -163.44
#   },

    erlang = ErlangC(transactions=231, asa=30, aht=447.4, interval=15 * 60, shrinkage=0.0)
    asa = erlang.what_asa(81)
    print(asa)

    service_level = erlang.service_level(81, scale_positions=False, asa=asa) * 100
    print(service_level)