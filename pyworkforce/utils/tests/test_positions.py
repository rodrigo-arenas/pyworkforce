from pyworkforce.utils.shift_spec import required_positions


def test_required_positions_14():
    positions = required_positions(
        call_volume=200, aht=180, interval=60*60, art=20, service_level=80
    )

    assert positions == 14


def test_required_positions_81():
    positions = required_positions(
        call_volume=202, aht=330, interval=15*60, art=30, service_level=80
    )

    assert positions == 81