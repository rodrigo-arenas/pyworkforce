# Scheduling

Once you know **how many resources are required per period** (for example, from
the [queuing](/guide/erlangc) step), scheduling decides **how many people to
place on each predefined shift**.

pyworkforce provides two constraint-programming solvers, both built on
[OR-Tools](https://developers.google.com/optimization):

- `MinAbsDifference` — minimize the total absolute difference between required
  and scheduled resources.
- `MinRequiredResources` — minimize the (optionally weighted) number of
  scheduled resources while ensuring every period is fully covered.

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
- `max_period_concurrency` and `max_shift_concurrency` are upper bounds. If
  they are too low, the solver may correctly return `INFEASIBLE`.
- Use `MinRequiredResources` when every period must be covered; use
  `MinAbsDifference` when matching demand closely is more important than strict
  coverage.
- Shift definitions drive feasibility. Validate `shifts_coverage` before
  assuming the demand pattern is impossible.
