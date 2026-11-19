---
description: Compare minimum staffing and minimum coverage gap with two Python shift schedulers built on OR-Tools. Try both with demand and shift coverage arrays.
---

# Shift Scheduling in Python with OR-Tools {#scheduling}

Given the headcount needed in each period, PyWorkforce calculates how many
people to assign to each predefined shift. The [worked Python example](#example)
runs both solvers on the same two-day demand and shift coverage arrays.

pyworkforce provides two constraint-programming solvers, both built on
[OR-Tools](https://developers.google.com/optimization):

- `MinAbsDifference` minimizes the total coverage gap, counting both overstaffing
  and understaffing. Use it when some shortfalls are acceptable.
- `MinRequiredResources` requires full coverage in every period. It minimizes
  scheduled headcount, or total shift cost if you supply weights.

For demand estimates, start with [Erlang C](/guide/erlangc). To assign named
employees after deciding how many are needed per shift, use [rostering](/guide/rostering).

## Inputs

Both solvers share the same core inputs:

| Argument | Description |
| --- | --- |
| `num_days` | Number of days to schedule |
| `periods` | Number of periods per day |
| `shifts_coverage` | `{shift_name: [0/1, …]}`, each array of length `periods` |
| `required_resources` | Array of shape `[num_days, periods]` |
| `max_period_concurrency` | Max resources allowed in any period |
| `max_shift_concurrency` | Max resources allowed on any single shift |
| `shift_limits` | Optional `(day, shift_name)` keys with inclusive `(minimum, maximum)` staffing bounds |

::: tip
Use the [shift coverage builders](/guide/shifts) to create `shifts_coverage`
instead of writing 0/1 arrays by hand. pyworkforce validates that every
coverage array and every `required_resources` row has exactly `periods`
entries, and raises a clear error otherwise.
:::

## Example

```python
from pyworkforce.scheduling import MinAbsDifference, MinRequiredResources

required_resources = [
    [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
    [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8],
]

shifts_coverage = {
    "Morning":   [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    "Night":     [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    "Mixed":     [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
}

difference = MinAbsDifference(
    num_days=2, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=27, max_shift_concurrency=25,
)
print(difference.solve()["status"])

requirements = MinRequiredResources(
    num_days=2, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=27, max_shift_concurrency=25,
)
print(requirements.solve()["status"])
```

## The solution

`solve()` returns a dictionary and also stores it on the estimator as
`solution_`:

```python
{
  "status": "OPTIMAL",
  "cost": 157.0,
  "resources_shifts": [
    {"day": 0, "shift": "Morning",   "resources": 8},
    {"day": 0, "shift": "Afternoon", "resources": 11},
    ...
  ],
}
```

- `status` — `OPTIMAL`, `FEASIBLE` or `INFEASIBLE`.
- `cost` — final objective value (`-1` when infeasible).
- `resources_shifts` — resources to assign per day and shift.

## Weighting shifts (MinRequiredResources)

By default every shift costs `1`. Pass a `cost_dict` to make some shifts more
expensive than others (for example, night shifts):

```python
cost_dict = {"Morning": 8, "Afternoon": 8, "Night": 10, "Mixed": 7}

scheduler = MinRequiredResources(
    num_days=2, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    cost_dict=cost_dict,
    max_period_concurrency=27, max_shift_concurrency=25,
)
```

`cost_dict` must contain exactly the same shift names as `shifts_coverage`.

## Search control

Both solvers accept `max_search_time` (seconds, default `120`/`240`) and
`num_search_workers` (default `2`) to bound the optimization.

## Common pitfalls

- `required_resources` must have one row per day and exactly `periods` values
  per row.
- `max_period_concurrency` and `max_shift_concurrency` are upper bounds.
  `MinRequiredResources` returns `INFEASIBLE` if those bounds prevent full
  coverage. `MinAbsDifference` reports a shortfall when the bounds allow a
  partial plan. Conflicting staffing limits can make either solver infeasible.
- Use `MinRequiredResources` when every period must be covered; use
  `MinAbsDifference` when matching demand closely is more important than strict
  coverage.
- Shift definitions drive feasibility. Validate `shifts_coverage` before
  assuming the demand pattern is impossible.

Use [`coverage()` and `compare_coverage()`](/guide/coverage-scenarios) to inspect
the periods that the solved plan covers and compare it with alternate demand.
