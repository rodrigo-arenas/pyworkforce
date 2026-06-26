"""Run the end-to-end tutorial and capture real outputs for the docs."""
from pyworkforce.queuing import ErlangC, ErlangA
from pyworkforce.shifts import shift_coverage_from_hours, coverage_to_dataframe
from pyworkforce.scheduling import MinRequiredResources
from pyworkforce.rostering import MinHoursRoster


def banner(title):
    print("\n# " + title)


calls_per_hour = [
    12, 8, 6, 5, 5, 8, 20, 45, 70, 85, 90, 88,
    80, 78, 82, 80, 70, 60, 48, 40, 32, 26, 20, 15,
]

banner("Step 1 - required positions per hour")
required_c, required_a = [], []
for calls in calls_per_hour:
    c = ErlangC(transactions=calls, aht=4, asa=20 / 60, interval=60, shrinkage=0.3)
    required_c.append(c.required_positions(service_level=0.8, max_occupancy=0.85)["positions"])
    a = ErlangA(transactions=calls, aht=4, asa=20 / 60, interval=60, patience=8, shrinkage=0.3)
    required_a.append(a.required_positions(service_level=0.8, max_occupancy=0.85)["positions"])
print("Erlang C:", required_c)
print("Erlang A:", required_a)
print("Total agent-hours  C:", sum(required_c), " A:", sum(required_a))

banner("Step 2 - shift coverage")
shifts_coverage = shift_coverage_from_hours({
    "Early": (6, 14),
    "Day":   (9, 17),
    "Late":  (13, 21),
    "Night": (21, 6),
}, num_periods=24)
print(coverage_to_dataframe(shifts_coverage).to_string())

banner("Step 3 - schedule onto shifts")
scheduler = MinRequiredResources(
    num_days=1, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=[required_c],
    max_period_concurrency=40, max_shift_concurrency=30,
)
schedule = scheduler.solve()
print("status:", schedule["status"], "| total agents (cost):", schedule["cost"])
for item in schedule["resources_shifts"]:
    print(item)

banner("Step 4 - roster named agents (small illustration)")
roster = MinHoursRoster(
    num_days=2,
    resources=["ana@co", "ben@co", "cara@co", "dan@co", "eve@co", "finn@co", "gil@co"],
    shifts=["Early", "Late", "Night"],
    shifts_hours=[8, 8, 9],
    min_working_hours=8,
    max_resting=1,
    required_resources={"Early": [2, 2], "Late": [2, 2], "Night": [1, 1]},
    banned_shifts=[{"resource": "ana@co", "shift": "Night", "day": 0}],
    resources_preferences=[{"resource": "ana@co", "shift": "Early"}],
)
sol = roster.solve()
print("status:", sol["status"], "| shifted_hours:", sol["shifted_hours"],
      "| resting_days:", sol["resting_days"])
for a in sol["resource_shifts"]:
    print(a)
