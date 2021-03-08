from pyworkforce.queuing.erlang import ErlangC


def test_expected_erlangc_results():
    erlang = ErlangC(transactions=100, asa=0.33, aht=3, interval=30, shrinkage=0.3)
    results = erlang.required_positions(service_level=0.8)
    raw_positions = results['raw_positions']
    positions = results['positions']
    service_level = results['service_level']
    occupancy = results['occupancy']

    assert raw_positions == 14
    assert positions == 20
    assert round(service_level, 3) == 0.888
    assert round(occupancy, 3) == 0.714

