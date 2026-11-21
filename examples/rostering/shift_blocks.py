"""Keep a shift through a day off, then allow a new shift in the final block."""

from pyworkforce.rostering import MinHoursRoster

resources = ["Operator A", "Operator B"]
demand = [1, 1, 1, 0, 1, 1, 1, 1, 1, 1]
roster = MinHoursRoster(
    num_days=10,
    resources=resources,
    shifts=["Early", "Late"],
    shifts_hours=[8, 8],
    min_working_hours=72,
    max_resting=1,
    required_resources={"Early": demand, "Late": demand},
    banned_shifts=[
        {"resource": "Operator A", "shift": "Late", "day": 0},
        {"resource": "Operator A", "shift": "Early", "day": 7},
    ],
    shift_block_starts=[0, 7],
)

solution = roster.solve()
if solution["status"] not in {"FEASIBLE", "OPTIMAL"}:
    raise RuntimeError(solution["status"])
assignments = {(item["resource"], item["day"]): item["shift"] for item in solution["resource_shifts"]}
for person in resources:
    days = [assignments.get((person, day), "Off") for day in range(roster.num_days)]
    print(f"{person} | {' '.join(days[:7])} | {' '.join(days[7:])}")
