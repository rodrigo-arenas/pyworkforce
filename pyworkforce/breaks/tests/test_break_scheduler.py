import pytest

from pyworkforce.breaks import BreakScheduler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_on_break(break_schedule, shifts_coverage, periods, num_days):
    """Return on_break[day][period] = number of slots on break at that point."""
    on_break = [[0] * periods for _ in range(num_days)]
    for entry in break_schedule:
        s = entry["shift"]
        d = entry["day"]
        start = entry["start_period"]
        end = entry["end_period"]
        cov = shifts_coverage[s]
        for p in range(start, end):
            if 0 <= p < periods and cov[p] == 1:
                on_break[d][p] += 1
    return on_break


def _overlaps_within_slot(break_schedule):
    """Return True if any two breaks in the same (shift, day, slot) overlap."""
    from collections import defaultdict
    slots = defaultdict(list)
    for entry in break_schedule:
        key = (entry["shift"], entry["day"], entry["slot"])
        slots[key].append((entry["start_period"], entry["end_period"]))
    for intervals in slots.values():
        intervals.sort()
        for k in range(len(intervals) - 1):
            if intervals[k][1] > intervals[k + 1][0]:
                return True
    return False


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_single_shift_single_break_feasible():
    """4 agents on an 8-period shift; 1-period break; slack=1 → spread across 4 periods."""
    shifts_coverage = {"Morning": [1, 1, 1, 1, 1, 1, 1, 1]}
    scheduled_resources = {"Morning": [4]}
    breaks = [{"name": "Short", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}]
    # valid starts: [1, 2, 3, 4, 5, 6]; need 4 slots, at most 1 concurrent → trivially feasible
    min_coverage = [[3, 3, 3, 3, 3, 3, 3, 3]]

    scheduler = BreakScheduler(
        num_days=1, periods=8,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["break_schedule"]) == 4  # 4 slots × 1 break

    on_break = _count_on_break(result["break_schedule"], shifts_coverage, 8, 1)
    for p in range(8):
        assert on_break[0][p] <= 1, f"coverage violated at period {p}"

    # Breaks must fall within valid start window [1, 6]
    for entry in result["break_schedule"]:
        assert 1 <= entry["start_period"] <= 6


def test_multiple_breaks_per_slot_no_overlap():
    """2 agents, 2 breaks each; verify no-overlap and coverage."""
    shifts_coverage = {"Day": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}
    scheduled_resources = {"Day": [2]}
    breaks = [
        {"name": "Short1", "duration_periods": 1, "min_start_after": 1, "max_end_before": 2},
        {"name": "Short2", "duration_periods": 1, "min_start_after": 1, "max_end_before": 2},
    ]
    # valid starts: [1, 7]; 2 breaks per slot can start anywhere in [1,7] without overlap
    min_coverage = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]  # slack = 1

    scheduler = BreakScheduler(
        num_days=1, periods=10,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["break_schedule"]) == 4  # 2 slots × 2 breaks

    assert not _overlaps_within_slot(result["break_schedule"])

    on_break = _count_on_break(result["break_schedule"], shifts_coverage, 10, 1)
    for p in range(10):
        assert on_break[0][p] <= 1


def test_multi_day_multi_shift():
    """2 days, 2 shifts; verify each day's coverage independently."""
    shifts_coverage = {
        "Morning": [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        "Afternoon": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
    }
    scheduled_resources = {
        "Morning": [3, 3],
        "Afternoon": [3, 3],
    }
    breaks = [{"name": "Lunch", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}]
    min_coverage = [
        [0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        [0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    ]

    scheduler = BreakScheduler(
        num_days=2, periods=12,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["break_schedule"]) == 2 * 2 * 3  # 2 days × 2 shifts × 3 slots

    on_break = _count_on_break(result["break_schedule"], shifts_coverage, 12, 2)
    total_scheduled = [[0] * 12 for _ in range(2)]
    for s, cov in shifts_coverage.items():
        for d in range(2):
            for p in range(12):
                if cov[p] == 1:
                    total_scheduled[d][p] += scheduled_resources[s][d]

    for d in range(2):
        for p in range(12):
            slack = total_scheduled[d][p] - min_coverage[d][p]
            assert on_break[d][p] <= slack, f"coverage violated at day={d}, period={p}"


def test_solution_stored_on_instance():
    shifts_coverage = {"Morning": [1, 1, 1, 1, 1, 1]}
    scheduled_resources = {"Morning": [2]}
    breaks = [{"name": "Rest", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}]
    min_coverage = [[1, 1, 1, 1, 1, 1]]

    scheduler = BreakScheduler(
        num_days=1, periods=6,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()
    assert scheduler.solution_ is result


def test_zero_slots_on_one_day():
    """When scheduled_resources is 0 for a day, no breaks are created for it."""
    shifts_coverage = {"Morning": [1, 1, 1, 1, 1, 1]}
    scheduled_resources = {"Morning": [3, 0]}
    breaks = [{"name": "Short", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}]
    min_coverage = [
        [2, 2, 2, 2, 2, 2],
        [0, 0, 0, 0, 0, 0],
    ]

    scheduler = BreakScheduler(
        num_days=2, periods=6,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    day1_entries = [e for e in result["break_schedule"] if e["day"] == 1]
    assert len(day1_entries) == 0


# ---------------------------------------------------------------------------
# Infeasible test
# ---------------------------------------------------------------------------

def test_infeasible_no_slack():
    """Coverage = scheduled: zero slack means no break can occur → INFEASIBLE."""
    shifts_coverage = {"Morning": [1, 1, 1, 1, 1, 1, 1, 1]}
    scheduled_resources = {"Morning": [4]}
    breaks = [{"name": "Short", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}]
    min_coverage = [[4, 4, 4, 4, 4, 4, 4, 4]]  # slack = 0 everywhere

    scheduler = BreakScheduler(
        num_days=1, periods=8,
        shifts_coverage=shifts_coverage,
        scheduled_resources=scheduled_resources,
        breaks=breaks,
        min_coverage=min_coverage,
    )
    result = scheduler.solve()

    assert result["status"] == "INFEASIBLE"
    assert result["cost"] == -1
    assert len(result["break_schedule"]) == 1
    assert result["break_schedule"][0]["shift"] == "Unknown"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_missing_scheduled_resources_key():
    with pytest.raises(ValueError, match="missing keys"):
        BreakScheduler(
            num_days=1, periods=8,
            shifts_coverage={"Morning": [1] * 8, "Night": [0] * 8},
            scheduled_resources={"Morning": [3]},
            breaks=[{"name": "Rest", "duration_periods": 1}],
            min_coverage=[[2] * 8],
        )


def test_wrong_scheduled_resources_length():
    with pytest.raises(ValueError, match="length"):
        BreakScheduler(
            num_days=2, periods=8,
            shifts_coverage={"Morning": [1] * 8},
            scheduled_resources={"Morning": [3]},  # should be length 2
            breaks=[{"name": "Rest", "duration_periods": 1}],
            min_coverage=[[2] * 8, [2] * 8],
        )


def test_break_does_not_fit_in_shift():
    with pytest.raises(ValueError, match="cannot fit"):
        BreakScheduler(
            num_days=1, periods=8,
            shifts_coverage={"Morning": [1, 1, 1, 1, 0, 0, 0, 0]},  # 4-period shift
            scheduled_resources={"Morning": [3]},
            breaks=[{"name": "Long", "duration_periods": 3,
                      "min_start_after": 1, "max_end_before": 1}],
            min_coverage=[[2] * 8],
        )


def test_duplicate_break_names():
    with pytest.raises(ValueError, match="unique"):
        BreakScheduler(
            num_days=1, periods=8,
            shifts_coverage={"Morning": [1] * 8},
            scheduled_resources={"Morning": [3]},
            breaks=[
                {"name": "Rest", "duration_periods": 1},
                {"name": "Rest", "duration_periods": 2},
            ],
            min_coverage=[[2] * 8],
        )


def test_min_coverage_exceeds_scheduled_raises():
    scheduler = BreakScheduler(
        num_days=1, periods=8,
        shifts_coverage={"Morning": [1] * 8},
        scheduled_resources={"Morning": [3]},
        breaks=[{"name": "Short", "duration_periods": 1, "min_start_after": 1, "max_end_before": 1}],
        min_coverage=[[5, 5, 5, 5, 5, 5, 5, 5]],  # exceeds scheduled=3
    )
    with pytest.raises(ValueError, match="exceeds"):
        scheduler.solve()


def test_get_params():
    scheduler = BreakScheduler(
        num_days=1, periods=8,
        shifts_coverage={"Morning": [1] * 8},
        scheduled_resources={"Morning": [3]},
        breaks=[{"name": "Short", "duration_periods": 1}],
        min_coverage=[[2] * 8],
    )
    params = scheduler.get_params()
    assert params["num_days"] == 1
    assert params["periods"] == 8
    assert params["max_search_time"] == 120.0
