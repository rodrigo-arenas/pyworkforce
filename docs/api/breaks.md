# API — Breaks

`pyworkforce.breaks`

## BreakScheduler

```python
BreakScheduler(
    num_days,
    periods,
    shifts_coverage,
    scheduled_resources,
    breaks,
    min_coverage,
    max_search_time=120.0,
    num_search_workers=2,
)
```

Schedules breaks for agent slots within each shift to maintain minimum
coverage throughout the planning horizon. Each shift/day combination has
`scheduled_resources[shift][day]` anonymous agent slots; the solver assigns a
start period to every break for every slot while enforcing break windows,
non-overlap, and coverage constraints.

**Parameters**

- **num_days** (`int`) — number of days in the planning horizon.
- **periods** (`int`) — number of periods per day (e.g. `48` for 30-minute slots
  in a 24-hour day).
- **shifts_coverage** (`dict`) — `{"shift_name": coverage_array}` where
  `coverage_array` has length `periods` and uses `1` when the shift is active,
  `0` otherwise.
- **scheduled_resources** (`dict`) — `{"shift_name": [count_day0, count_day1, …]}`
  with the number of agent slots per shift per day (typically the output of the
  scheduling step).
- **breaks** (`list[dict]`) — break definitions. Each dict must have:
  - `name` (`str`) — unique identifier.
  - `duration_periods` (`int`) — break length in periods.
  - `min_start_after` (`int`, default `0`) — periods into the shift before the
    break may start.
  - `max_end_before` (`int`, default `0`) — periods remaining in the shift after
    the break must finish.
- **min_coverage** (`list`) — 2-D array `[num_days][periods]` — minimum agents
  that must remain available (not on break) at each period.
- **max_search_time** (`float`, default `120.0`) — maximum solver wall-clock
  time in seconds.
- **num_search_workers** (`int`, default `2`) — number of parallel search workers.

**Attributes**

- **solution_** (`dict` or `None`) — the last result returned by `solve()`,
  or `None` if `solve()` has not been called.

**Methods**

- `solve()` → `dict`

  Run the CP-SAT solver and return a result dict with:

  - `status` (`str`) — `"OPTIMAL"`, `"FEASIBLE"`, or `"INFEASIBLE"`.
  - `cost` (`float`) — objective value (`0.0` for optimal/feasible; `-1` when
    infeasible).
  - `break_schedule` (`list[dict]`) — one entry per `(shift, day, slot, break)`.
    Each entry contains `shift`, `day`, `slot`, `break_name`, `start_period`
    (inclusive) and `end_period` (exclusive).

- `get_params()` → `dict`

See the [Break scheduling guide](/guide/breaks).
