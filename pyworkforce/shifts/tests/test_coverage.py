import pytest

from pyworkforce.shifts import (
    coverage_to_dataframe,
    shift_coverage_from_hours,
    shift_coverage_from_periods,
    shift_coverage_from_spans,
    validate_shift_coverage,
)


def test_from_periods_basic():
    cov = shift_coverage_from_periods({"Morning": [0, 1, 2]}, num_periods=4)
    assert cov == {"Morning": [1, 1, 1, 0]}


def test_from_periods_rejects_out_of_range():
    with pytest.raises(ValueError):
        shift_coverage_from_periods({"M": [0, 5]}, num_periods=4)


def test_from_periods_rejects_non_integer():
    with pytest.raises(ValueError):
        shift_coverage_from_periods({"M": [0, 1.5]}, num_periods=4)


def test_from_spans_single_tuple():
    cov = shift_coverage_from_spans({"Day": (1, 2)}, num_periods=4)
    assert cov == {"Day": [0, 1, 1, 0]}


def test_from_spans_wraparound():
    cov = shift_coverage_from_spans({"Night": (3, 3)}, num_periods=4)
    assert cov == {"Night": [1, 1, 0, 1]}


def test_from_spans_no_wraparound_raises():
    with pytest.raises(ValueError):
        shift_coverage_from_spans({"Night": (3, 3)}, num_periods=4, wrap_around=False)


def test_from_spans_multiple_blocks():
    cov = shift_coverage_from_spans({"Split": [(0, 1), (3, 1)]}, num_periods=4)
    assert cov == {"Split": [1, 0, 0, 1]}


def test_from_hours_matches_handwritten_readme_coverage():
    cov = shift_coverage_from_hours({
        "Morning": (5, 13),
        "Afternoon": (13, 21),
        "Night": (21, 5),
        "Mixed": (9, 17),
    }, num_periods=24)

    expected = {
        "Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
        "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
        "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    }
    assert cov == expected


def test_from_hours_half_hour_granularity():
    cov = shift_coverage_from_hours({"Early": (8, 8.5)}, num_periods=48, period_minutes=30)
    assert sum(cov["Early"]) == 1
    assert cov["Early"][16] == 1


def test_from_hours_rejects_misaligned_window():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({"Bad": (8.25, 9)}, num_periods=24, period_minutes=60)


def test_from_hours_rejects_bad_period_product():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({"M": (8, 9)}, num_periods=10, period_minutes=60)


def test_validate_shift_coverage_ok():
    assert validate_shift_coverage({"A": [1, 0, 1], "B": [0, 1, 0]}) == 3


def test_validate_shift_coverage_inconsistent_lengths():
    with pytest.raises(ValueError):
        validate_shift_coverage({"A": [1, 0, 1], "B": [0, 1]})


def test_validate_shift_coverage_non_binary():
    with pytest.raises(ValueError):
        validate_shift_coverage({"A": [1, 2, 0]})


def test_coverage_to_dataframe_shape():
    df = coverage_to_dataframe({"A": [1, 0, 1], "B": [0, 1, 0]})
    assert list(df.index) == ["A", "B"]
    assert df.shape == (2, 3)


def test_from_periods_rejects_empty_dict():
    with pytest.raises(ValueError):
        shift_coverage_from_periods({}, num_periods=4)


def test_from_spans_rejects_empty_dict():
    with pytest.raises(ValueError):
        shift_coverage_from_spans({}, num_periods=4)


def test_from_spans_rejects_out_of_range_start():
    with pytest.raises(ValueError):
        shift_coverage_from_spans({"M": (5, 1)}, num_periods=4)


def test_from_spans_rejects_non_positive_length():
    with pytest.raises(ValueError):
        shift_coverage_from_spans({"M": (0, 0)}, num_periods=4)


def test_from_spans_rejects_non_integer_start_in_list():
    with pytest.raises(ValueError) as excinfo:
        shift_coverage_from_spans({"M": [(1.5, 1)]}, num_periods=4)
    assert "non-integer start" in str(excinfo.value)


def test_from_hours_rejects_empty_dict():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({}, num_periods=24)


def test_from_hours_rejects_hour_out_of_range():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({"M": (8, 30)}, num_periods=24)


def test_from_hours_overnight_without_wraparound_raises():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({"Night": (22, 6)}, num_periods=24, wrap_around=False)


def test_from_hours_zero_length_window_raises():
    with pytest.raises(ValueError):
        shift_coverage_from_hours({"M": (8, 8)}, num_periods=24)


def test_validate_rejects_empty():
    with pytest.raises(ValueError):
        validate_shift_coverage({})


def test_builders_feed_scheduler():
    from pyworkforce.scheduling import MinRequiredResources

    # Two 12-hour shifts that together cover the whole day.
    shifts_coverage = shift_coverage_from_hours({
        "Day": (6, 18), "Night": (18, 6),
    }, num_periods=24)
    required_resources = [[3] * 24, [4] * 24]

    scheduler = MinRequiredResources(num_days=2, periods=24,
                                     shifts_coverage=shifts_coverage,
                                     required_resources=required_resources,
                                     max_period_concurrency=30,
                                     max_shift_concurrency=30)
    solution = scheduler.solve()
    assert solution["status"] in ("OPTIMAL", "FEASIBLE")
