import pytest

from pyworkforce.rostering import MinHoursRoster


def roster_for(shifts_by_day, **options):
    shifts = ["Early", "Late", "Night"]
    days = len(shifts_by_day)
    return MinHoursRoster(
        num_days=days, resources=["A"], shifts=shifts, shifts_hours=[8] * len(shifts),
        required_resources={shift: [int(demand == shift) for demand in shifts_by_day] for shift in shifts},
        min_working_hours=8, max_resting=days - 1, banned_shifts=None, **options,
    )


def test_weekly_block_allows_days_off_and_a_change_in_the_partial_final_week():
    demand = ["Early", "Early", None, "Early", "Early", "Early", "Early", "Late", None, "Late"]
    roster = roster_for(demand, shift_block_starts=[0, 7])
    solution = roster.solve()
    assert solution["status"] == "OPTIMAL"
    assert [r["day"] for r in solution["resting_resource"]] == [2, 8]
    assert [(r["day"], r["shift"]) for r in solution["resource_shifts"]] == [
        (day, shift) for day, shift in enumerate(demand) if shift
    ]
    assert roster.get_params()["shift_block_starts"] == (0, 7)


def test_day_off_does_not_reset_the_block_but_a_boundary_permits_a_change():
    demand = ["Early", None, "Night"]
    assert roster_for(demand).solve()["status"] == "OPTIMAL"
    assert roster_for(demand, shift_block_starts=[0]).solve()["status"] == "INFEASIBLE"
    assert roster_for(demand, shift_block_starts=[0, 2]).solve()["status"] == "OPTIMAL"


def test_blocks_are_per_person_and_respect_bans_hours_and_soft_preferences():
    roster = MinHoursRoster(
        4, ["A", "B"], ["Early", "Late"], [8, 8], 32,
        [{"resource": "A", "shift": "Late", "day": 2}], 1,
        {"Early": [1] * 4, "Late": [1] * 4},
        resources_preferences=[{"resource": "A", "shift": "Late"}], shift_block_starts=[0, 2],
    )
    solution = roster.solve()
    assert solution["status"] == "OPTIMAL"
    assert solution["shifted_hours"] == 64
    assert [r["shift"] for r in solution["resource_shifts"] if r["resource"] == "A"] == ["Late"] * 2 + ["Early"] * 2
    assert [r["shift"] for r in solution["resource_shifts"] if r["resource"] == "B"] == ["Early"] * 2 + ["Late"] * 2


def test_entire_block_can_be_off_and_boundary_allows_repeating_a_shift():
    demand = ["Early", None, None, "Early", "Early"]
    result = roster_for(demand, shift_block_starts=[0, 1, 3, 4]).solve()
    assert result["status"] == "OPTIMAL"
    assert [r["day"] for r in result["resting_resource"]] == [1, 2]
    assert [r["shift"] for r in result["resource_shifts"]] == ["Early"] * 3


@pytest.mark.parametrize("starts", [None, [0, 2]])
@pytest.mark.parametrize(("demand", "status"), [
    (["Night", "Night", "Night"], "OPTIMAL"),
    (["Night", "Night", "Early"], "INFEASIBLE"),
    (["Night", "Night", "Late"], "INFEASIBLE"),
    (["Night", None, "Early"], "OPTIMAL"),
])
def test_only_listed_next_day_transitions_are_banned(demand, status, starts):
    bans = [{"origin": "Night", "destination": destination} for destination in ("Early", "Late")]
    solution = roster_for(demand, shift_block_starts=starts, non_sequential_shifts=bans).solve()
    assert solution["status"] == status


@pytest.mark.parametrize("starts", [[], [1], [0, 0], [0, 2, 1], [0, 3], [0, -1], [False], [0, 1.5], 7, "01"])
def test_rejects_invalid_block_boundaries(starts):
    with pytest.raises(ValueError, match="shift_block_starts"):
        roster_for(["Early"] * 3, shift_block_starts=starts)
