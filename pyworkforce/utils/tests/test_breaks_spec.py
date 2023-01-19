from pyworkforce.utils.breaks_spec import build_intervals_map


def test_build_intervals_map():
    m, t = build_intervals_map(15)

    print(m)

    assert len(m) == 96
    assert len(t) == 96

    assert m['00:00'] == 0
    assert m['00:15'] == 1
    assert m['23:45'] == 95

    assert t[0] == "00:00"
    assert t[4] == "01:00"
