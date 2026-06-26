import pytest

from pyworkforce.queuing import ErlangB, MultiErlangB

# ---------------------------------------------------------------------------
# ErlangB – known analytical values
# ---------------------------------------------------------------------------

def test_blocking_probability_c1_a1():
    # B(1, A=1) = 1/(1+1) = 0.5 (exact)
    erlang = ErlangB(transactions=30, aht=1, interval=30)  # intensity = 1.0
    assert round(erlang.blocking_probability(1), 6) == 0.5


def test_blocking_probability_c2_a1():
    # B(2, A=1) = (1^2/2!) / (1 + 1 + 0.5) = 0.5/2.5 = 0.2 (exact)
    erlang = ErlangB(transactions=30, aht=1, interval=30)  # intensity = 1.0
    assert round(erlang.blocking_probability(2), 6) == 0.2


def test_blocking_probability_decreases_with_more_positions():
    erlang = ErlangB(transactions=100, aht=3, interval=30)  # intensity = 10.0
    prev = 1.0
    for c in range(1, 20):
        b = erlang.blocking_probability(c)
        assert b < prev, f"blocking probability did not decrease at c={c}"
        prev = b


def test_blocking_probability_approaches_zero():
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    assert erlang.blocking_probability(50) < 1e-6


def test_blocking_probability_scale_positions():
    # With shrinkage=0.3, scale_positions=True: productive = floor(0.7 * 20) = 14
    erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    b_scaled = erlang.blocking_probability(positions=20, scale_positions=True)
    b_raw = erlang.blocking_probability(positions=14, scale_positions=False)
    assert round(b_scaled, 10) == round(b_raw, 10)


def test_achieved_occupancy_no_blocking():
    # When blocking → 0, occupancy → A/c
    erlang = ErlangB(transactions=100, aht=3, interval=30)  # A=10
    occ = erlang.achieved_occupancy(50)
    assert abs(occ - 10 / 50) < 1e-4


def test_achieved_occupancy_is_between_0_and_1():
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    for c in range(1, 25):
        occ = erlang.achieved_occupancy(c)
        assert 0 <= occ <= 1, f"occupancy out of range at c={c}"


def test_achieved_occupancy_scale_positions():
    erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    occ_scaled = erlang.achieved_occupancy(positions=20, scale_positions=True)
    occ_raw = erlang.achieved_occupancy(positions=14, scale_positions=False)
    assert round(occ_scaled, 10) == round(occ_raw, 10)


# ---------------------------------------------------------------------------
# ErlangB.required_positions
# ---------------------------------------------------------------------------

def test_required_positions_known_value():
    # A=10 Erlangs, max_blocking=0.02 → raw_positions=17 (verified by recursion)
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    result = erlang.required_positions(max_blocking=0.02)
    assert result["raw_positions"] == 17
    assert result["blocking_probability"] <= 0.02
    assert result["blocking_probability"] > 0


def test_required_positions_with_shrinkage():
    # raw_positions stays 17; positions = ceil(17/0.7) = 25
    erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    result = erlang.required_positions(max_blocking=0.02)
    assert result["raw_positions"] == 17
    assert result["positions"] == 25


def test_required_positions_tight_blocking():
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    result = erlang.required_positions(max_blocking=0.001)
    # Tighter target → more positions needed
    result_loose = erlang.required_positions(max_blocking=0.02)
    assert result["raw_positions"] > result_loose["raw_positions"]


def test_required_positions_max_occupancy_binding():
    # Forcing low occupancy requires more trunks than blocking alone
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    result_no_occ = erlang.required_positions(max_blocking=0.05)
    result_with_occ = erlang.required_positions(max_blocking=0.05, max_occupancy=0.5)
    assert result_with_occ["raw_positions"] >= result_no_occ["raw_positions"]
    assert result_with_occ["occupancy"] <= 0.5


def test_required_positions_result_keys():
    erlang = ErlangB(transactions=60, aht=2, interval=30)
    result = erlang.required_positions(max_blocking=0.05)
    for key in ("raw_positions", "positions", "blocking_probability", "occupancy"):
        assert key in result


def test_required_positions_zero_blocking_target():
    # max_blocking=0 means B must be exactly 0, impossible in finite c → find the
    # point where blocking rounds to 0.0 in float precision
    erlang = ErlangB(transactions=10, aht=1, interval=30)
    result = erlang.required_positions(max_blocking=0.0)
    # blocking must be ≤ 0, so effectively 0 (should still find a result)
    assert result["blocking_probability"] <= 0.0


def test_intensity_attribute():
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    assert erlang.intensity == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_negative_transactions():
    with pytest.raises(ValueError, match="transactions"):
        ErlangB(transactions=-1, aht=3, interval=30)


def test_zero_aht():
    with pytest.raises(ValueError, match="aht"):
        ErlangB(transactions=100, aht=0, interval=30)


def test_invalid_shrinkage_high():
    with pytest.raises(ValueError):
        ErlangB(transactions=100, aht=3, interval=30, shrinkage=1.0)


def test_zero_productive_positions():
    erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    with pytest.raises(ValueError, match="productive positions"):
        erlang.blocking_probability(positions=0)


def test_invalid_max_blocking():
    erlang = ErlangB(transactions=100, aht=3, interval=30)
    with pytest.raises(ValueError):
        erlang.required_positions(max_blocking=1.5)


# ---------------------------------------------------------------------------
# MultiErlangB
# ---------------------------------------------------------------------------

def test_multi_erlang_b_blocking_probability():
    param_grid = {
        "transactions": [60, 90],
        "aht": [3],
        "interval": [30],
        "shrinkage": [0.0],
    }
    multi = MultiErlangB(param_grid=param_grid, n_jobs=1)
    results = multi.blocking_probability({"positions": [10, 15]})

    assert len(results) == 4  # 2 param combos × 2 positions
    assert all(0 <= r <= 1 for r in results)
    assert multi.blocking_probability_params is not None
    assert len(multi.blocking_probability_params) == 4


def test_multi_erlang_b_required_positions():
    param_grid = {
        "transactions": [60, 90],
        "aht": [3],
        "interval": [30],
    }
    multi = MultiErlangB(param_grid=param_grid, n_jobs=1)
    results = multi.required_positions({"max_blocking": [0.02, 0.05]})

    assert len(results) == 4  # 2 param combos × 2 max_blocking values
    for r in results:
        assert "raw_positions" in r
        assert r["blocking_probability"] >= 0


def test_multi_erlang_b_achieved_occupancy():
    param_grid = {"transactions": [60], "aht": [2], "interval": [30]}
    multi = MultiErlangB(param_grid=param_grid, n_jobs=1)
    results = multi.achieved_occupancy({"positions": [8, 10, 12]})

    assert len(results) == 3
    assert all(0 <= r <= 1 for r in results)


def test_multi_erlang_b_params_stored():
    param_grid = {"transactions": [60], "aht": [2], "interval": [30]}
    multi = MultiErlangB(param_grid=param_grid, n_jobs=1)
    multi.achieved_occupancy({"positions": [8, 10]})
    assert multi.achieved_occupancy_params is not None


def test_get_params_erlang_b():
    erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    params = erlang.get_params()
    assert params["transactions"] == 100
    assert params["aht"] == 3
    assert params["interval"] == 30
    assert params["shrinkage"] == 0.3
