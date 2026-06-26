import pytest

from pyworkforce.rostering import MinHoursRoster


BASE_KWARGS = dict(
    num_days=2,
    resources=["a", "b", "c"],
    shifts=["Morning", "Night"],
    shifts_hours=[8, 8],
    min_working_hours=8,
    banned_shifts=None,
    max_resting=1,
    required_resources={"Morning": [1, 1], "Night": [1, 1]},
)


def make(**overrides):
    kwargs = dict(BASE_KWARGS)
    kwargs.update(overrides)
    return MinHoursRoster(**kwargs)


def test_valid_construction_and_solution_attribute():
    roster = make()
    assert roster.solution_ is None
    solution = roster.solve()
    assert roster.solution_ == solution
    assert solution["status"] in ("OPTIMAL", "FEASIBLE")


def test_rejects_duplicate_resources():
    with pytest.raises(ValueError) as excinfo:
        make(resources=["a", "a", "b"])
    assert "unique" in str(excinfo.value)


def test_rejects_shift_hours_mismatch():
    with pytest.raises(ValueError) as excinfo:
        make(shifts_hours=[8])
    assert "shifts_hours" in str(excinfo.value)


def test_rejects_missing_required_resources_shift():
    with pytest.raises(ValueError) as excinfo:
        make(required_resources={"Morning": [1, 1]})
    assert "missing" in str(excinfo.value)


def test_rejects_required_resources_wrong_days():
    with pytest.raises(ValueError):
        make(required_resources={"Morning": [1, 1, 1], "Night": [1, 1, 1]})


def test_rejects_max_resting_ge_num_days():
    with pytest.raises(ValueError) as excinfo:
        make(max_resting=2)
    assert "max_resting" in str(excinfo.value)


def test_rejects_non_positive_min_working_hours():
    with pytest.raises(ValueError):
        make(min_working_hours=0)


def test_get_params_and_repr():
    roster = make()
    params = roster.get_params()
    assert params["num_days"] == 2
    assert params["resources"] == ["a", "b", "c"]
    assert repr(roster).startswith("MinHoursRoster(")
