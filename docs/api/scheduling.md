# API — Scheduling

`pyworkforce.scheduling`

Both schedulers share the same constructor signature (except `cost_dict`) and
the same `solve()` output. They validate that every `shifts_coverage` array and
every `required_resources` row has exactly `periods` entries.

## MinAbsDifference

```python
MinAbsDifference(num_days, periods, shifts_coverage, required_resources,
                 max_period_concurrency, max_shift_concurrency,
                 max_search_time=120.0, num_search_workers=2, *, shift_limits=None)
```

Minimizes the total absolute difference between required and scheduled
resources per period.

## MinRequiredResources

```python
MinRequiredResources(num_days, periods, shifts_coverage, required_resources,
                     max_period_concurrency, max_shift_concurrency,
                     cost_dict=None, max_search_time=240.0, num_search_workers=2,
                     *, shift_limits=None)
```

Minimizes the (optionally weighted) number of scheduled resources while
covering every period.

- **cost_dict** (`dict`, optional) — `{shift_name: cost}`; must contain exactly
  the same shift names as `shifts_coverage`. Defaults to a cost of `1` per
  shift.

## Daily shift limits

Both schedulers accept `shift_limits={(day, shift_name): (minimum, maximum)}`.
Days are zero-based and bounds are inclusive non-negative integers. The maximum
cannot exceed `max_shift_concurrency`. Unspecified pairs use the global bounds.
Fixed limits may still make the model infeasible, for example if their sum
exceeds `max_period_concurrency` during an overlap.

## Inspecting a solved schedule

These methods require the last `solve()` to have returned `OPTIMAL` or
`FEASIBLE`. Otherwise they raise `RuntimeError`.

- `scheduled_resources()` returns `{shift_name: [count_day_0, …]}` for
  `BreakScheduler` or other consumers.
- `coverage(required_resources=None)` returns a pandas DataFrame with `day`,
  `period`, `required`, `scheduled`, `shortfall`, and `surplus`. Each row
  represents one zero-based period on one zero-based day. Alternate demand must
  have shape `(num_days, periods)` and consist of non-negative 64-bit integers.
- `compare_coverage(scenarios)` takes a non-empty mapping of scenario names to
  demand arrays. Use `None` for the original forecast. Each scenario yields
  `required`, `scheduled`, `shortfall`, and `surplus` totals in person-periods,
  plus `understaffed_periods`. The assignments stay fixed throughout.

See the [schedule stress-test tutorial](/guide/coverage-scenarios).

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
