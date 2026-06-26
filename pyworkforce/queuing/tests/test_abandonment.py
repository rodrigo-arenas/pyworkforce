import pytest

from pyworkforce.queuing import ErlangA, ErlangC


def make_erlang(**overrides):
    params = dict(transactions=100, aht=3, asa=20 / 60, interval=30,
                  patience=5, shrinkage=0.0)
    params.update(overrides)
    return ErlangA(**params)


def test_erlanga_regression_metrics():
    """Snapshot of the exact stationary metrics for a fixed scenario."""
    erlang = make_erlang()

    metrics = erlang._metrics(14)
    assert round(metrics["waiting_probability"], 5) == 0.14526
    assert round(metrics["abandonment_probability"], 6) == 0.013984
    assert round(metrics["occupancy"], 6) == 0.704297
    assert round(metrics["average_speed_of_answer"], 6) == 0.069919
    assert round(erlang.service_level(14), 6) == 0.916792


def test_erlanga_matches_erlangc_in_patient_limit():
    """As patience grows the system converges to Erlang C."""
    erlang_a = make_erlang(patience=1_000_000, shrinkage=0.0)
    erlang_c = ErlangC(transactions=100, aht=3, asa=20 / 60, interval=30, shrinkage=0.0)

    for positions in (15, 20, 25):
        assert erlang_a.waiting_probability(positions) == pytest.approx(
            erlang_c.waiting_probability(positions), abs=1e-4)
        assert erlang_a.achieved_occupancy(positions) == pytest.approx(
            erlang_c.achieved_occupancy(positions), abs=1e-4)
        assert erlang_a.service_level(positions) == pytest.approx(
            erlang_c.service_level(positions), abs=1e-3)


def test_erlanga_littles_law_consistency():
    """Average speed of answer must equal queue length / arrival rate."""
    erlang = make_erlang()
    metrics = erlang._metrics(16)
    expected_asa = metrics["average_queue_length"] / erlang.arrival_rate
    assert metrics["average_speed_of_answer"] == pytest.approx(expected_asa)


def test_erlanga_probabilities_in_range():
    erlang = make_erlang()
    for positions in (14, 16, 20):
        assert 0 <= erlang.waiting_probability(positions) <= 1
        assert 0 <= erlang.abandonment_probability(positions) <= 1
        assert 0 <= erlang.achieved_occupancy(positions) <= 1
        assert 0 <= erlang.service_level(positions) <= 1


def test_erlanga_monotonic_service_level():
    """More positions cannot reduce the service level."""
    erlang = make_erlang()
    levels = [erlang.service_level(c) for c in range(14, 22)]
    assert all(b >= a - 1e-9 for a, b in zip(levels, levels[1:]))


def test_erlanga_less_patience_more_abandonment():
    """Impatient customers abandon more often, all else equal."""
    patient = make_erlang(patience=20)
    impatient = make_erlang(patience=1)
    assert impatient.abandonment_probability(14) > patient.abandonment_probability(14)


def test_erlanga_required_positions_meets_targets():
    erlang = make_erlang()
    result = erlang.required_positions(service_level=0.8, max_occupancy=0.85,
                                       max_abandonment=0.05)
    assert result["service_level"] >= 0.8
    assert result["occupancy"] <= 0.85
    assert result["abandonment_probability"] <= 0.05
    assert result["positions"] >= result["raw_positions"]


def test_erlanga_required_positions_shrinkage_scales_up():
    no_shrink = make_erlang(shrinkage=0.0).required_positions(service_level=0.8)
    shrink = make_erlang(shrinkage=0.3).required_positions(service_level=0.8)
    assert shrink["positions"] > no_shrink["positions"]
    assert shrink["raw_positions"] == no_shrink["raw_positions"]


def test_erlanga_service_level_custom_asa():
    erlang = make_erlang()
    quick = erlang.service_level(16, asa=5 / 60)
    relaxed = erlang.service_level(16, asa=60 / 60)
    assert relaxed >= quick


@pytest.mark.parametrize("bad_kwargs,message", [
    ({"transactions": -1}, "transactions must be a positive number"),
    ({"aht": 0}, "aht must be a positive number"),
    ({"patience": -3}, "patience must be a positive number"),
    ({"shrinkage": 1}, "shrinkage must be in the interval [0, 1)"),
])
def test_erlanga_invalid_construction(bad_kwargs, message):
    with pytest.raises(ValueError) as excinfo:
        make_erlang(**bad_kwargs)
    assert message in str(excinfo.value)


def test_erlanga_invalid_positions():
    erlang = make_erlang()
    with pytest.raises(ValueError):
        erlang.waiting_probability(0)
    with pytest.raises(ValueError):
        erlang.service_level(-2)


def test_erlanga_required_positions_invalid_targets():
    erlang = make_erlang()
    with pytest.raises(ValueError):
        erlang.required_positions(service_level=1.5)
    with pytest.raises(ValueError):
        erlang.required_positions(service_level=0.8, max_occupancy=0)
