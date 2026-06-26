"""
Build a ``shifts_coverage`` definition from clock hours instead of writing 0/1
arrays by hand, then feed it straight into a scheduler.
"""

from pyworkforce.shifts import shift_coverage_from_hours, coverage_to_dataframe
from pyworkforce.scheduling import MinRequiredResources

# Three eight-hour shifts that together cover the whole day.
shifts_coverage = shift_coverage_from_hours({
    "Morning":   (6, 14),
    "Afternoon": (14, 22),
    "Night":     (22, 6),   # overnight shift, wraps past midnight
}, num_periods=24)

print("Coverage:")
print(coverage_to_dataframe(shifts_coverage))

# Required resources per hour for two days.
required_resources = [
    [3, 3, 3, 3, 3, 3, 6, 6, 6, 6, 8, 8, 8, 8, 6, 6, 6, 6, 4, 4, 4, 4, 3, 3],
    [4, 4, 4, 4, 4, 4, 7, 7, 7, 7, 9, 9, 9, 9, 7, 7, 7, 7, 5, 5, 5, 5, 4, 4],
]

scheduler = MinRequiredResources(
    num_days=2,
    periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=30,
    max_shift_concurrency=30,
)

solution = scheduler.solve()
print("\nstatus:", solution["status"], "cost:", solution["cost"])
for item in solution["resources_shifts"]:
    print(item)
