"""Run from an installed development checkout with pyworkforce[plot]."""

from matplotlib import pyplot as plt

from pyworkforce.plotting import plot_period_shortfalls
from pyworkforce.scheduling import MinRequiredResources

base = [[2, 3, 1], [1, 2, 2]]
campaign = [[2, 3, 1], [2, 4, 2]]
scheduler = MinRequiredResources(
    num_days=2,
    periods=3,
    shifts_coverage={"early": [1, 1, 0], "late": [0, 1, 1]},
    required_resources=base,
    max_period_concurrency=3,
    max_shift_concurrency=3,
    shift_limits={(0, "early"): (2, 3), (0, "late"): (0, 1),
                  (1, "early"): (1, 1), (1, "late"): (2, 2)},
    num_search_workers=1,
)
solution = scheduler.solve()
if solution["status"] not in {"OPTIMAL", "FEASIBLE"}:
    raise RuntimeError(solution["status"])

late_rush = [[2, 3, 1], [1, 2, 4]]
scenarios = {"Base": None, "Campaign": campaign, "Late rush": late_rush}
shortfalls = scheduler.compare_coverage(scenarios, by_period=True)
print(shortfalls.to_string())

figure, ax = plt.subplots(figsize=(5.6, 2.8), layout="constrained")
plot_period_shortfalls(shortfalls, limit=3, ax=ax)
figure.savefig("period-shortfalls.png", dpi=150)
plt.close(figure)
