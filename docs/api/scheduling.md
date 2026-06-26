# API — Scheduling

`pyworkforce.scheduling`

Both schedulers share the same constructor signature (except `cost_dict`) and
the same `solve()` output. They validate that every `shifts_coverage` array and
every `required_resources` row has exactly `periods` entries.

## MinAbsDifference

```python
MinAbsDifference(num_days, periods, shifts_coverage, required_resources,
                 max_period_concurrency, max_shift_concurrency,
                 max_search_time=120.0, num_search_workers=2)
```

Minimizes the total absolute difference between required and scheduled
resources per period.

## MinRequiredResources

```python
MinRequiredResources(num_days, periods, shifts_coverage, required_resources,
                     max_period_concurrency, max_shift_concurrency,
                     cost_dict=None, max_search_time=240.0, num_search_workers=2)
```

Minimizes the (optionally weighted) number of scheduled resources while
covering every period.

- **cost_dict** (`dict`, optional) — `{shift_name: cost}`; must contain exactly
  the same shift names as `shifts_coverage`. Defaults to a cost of `1` per
  shift.

## Common parameters

- **num_days** (`int`) — days to schedule.
- **periods** (`int`) — periods per day.
- **shifts_coverage** (`dict`) — `{shift_name: [0/1, …]}`, length `periods`.
- **required_resources** (`list`) — shape `[num_days, periods]`.
- **max_period_concurrency** (`int`) — max resources per period.
- **max_shift_concurrency** (`int`) — max resources per shift.
- **max_search_time** (`float`) — solver time limit, seconds.
- **num_search_workers** (`int`) — solver worker threads.

## `solve()`

Returns a `dict` (also stored as `solution_`):

- **status** — `"OPTIMAL"`, `"FEASIBLE"` or `"INFEASIBLE"`.
- **cost** — objective value (`-1` if infeasible).
- **resources_shifts** — list of `{"day", "shift", "resources"}`.

See the [scheduling guide](/guide/scheduling).
