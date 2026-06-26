import pytest

from pyworkforce.scheduling import MinAbsDifference, MinRequiredResources


BASE_KWARGS = dict(
    num_days=2,
    periods=3,
    shifts_coverage={"A": [1, 1, 0], "B": [0, 0, 1]},
    required_resources=[[1, 1, 1], [2, 2, 2]],
    max_period_concurrency=10,
    max_shift_concurrency=10,
)


def make(cls=MinRequiredResources, **overrides):
    kwargs = dict(BASE_KWARGS)
    kwargs.update(overrides)
    return cls(**kwargs)


def test_valid_construction_stores_solution_attribute():
    scheduler = make()
    assert scheduler.solution_ is None
    solution = scheduler.solve()
    assert scheduler.solution_ == solution


@pytest.mark.parametrize("cls", [MinAbsDifference, MinRequiredResources])
def test_rejects_wrong_required_resources_rows(cls):
    with pytest.raises(ValueError) as excinfo:
        make(cls, required_resources=[[1, 1, 1]])  # only 1 day, num_days=2
    assert "required_resources" in str(excinfo.value)


@pytest.mark.parametrize("cls", [MinAbsDifference, MinRequiredResources])
def test_rejects_wrong_coverage_length(cls):
    with pytest.raises(ValueError) as excinfo:
        make(cls, shifts_coverage={"A": [1, 1], "B": [0, 0, 1]})
    assert "shifts_coverage" in str(excinfo.value)


@pytest.mark.parametrize("cls", [MinAbsDifference, MinRequiredResources])
def test_rejects_required_resources_row_wrong_length(cls):
    # Correct number of rows, but one row has the wrong number of periods.
    with pytest.raises(ValueError) as excinfo:
        make(cls, required_resources=[[1, 1, 1], [2, 2]])
    assert "required_resources[1]" in str(excinfo.value)


@pytest.mark.parametrize("cls", [MinAbsDifference, MinRequiredResources])
def test_rejects_non_positive_num_days(cls):
    with pytest.raises(ValueError):
        make(cls, num_days=0)


@pytest.mark.parametrize("cls", [MinAbsDifference, MinRequiredResources])
def test_rejects_empty_shifts_coverage(cls):
    with pytest.raises(ValueError):
        make(cls, shifts_coverage={})


def test_accepts_integer_max_search_time():
    # Previously rejected because the validator required a float instance.
    scheduler = make(max_search_time=120)
    assert scheduler.max_search_time == 120


def test_cost_dict_mismatch_raises():
    with pytest.raises(KeyError):
        make(MinRequiredResources, cost_dict={"A": 1})
