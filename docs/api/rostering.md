# API — Rostering

`pyworkforce.rostering`

## MinHoursRoster

```python
MinHoursRoster(num_days, resources, shifts, shifts_hours, min_working_hours,
               banned_shifts, max_resting, required_resources,
               non_sequential_shifts=None, resources_preferences=None,
               resources_prioritization=None,
               max_search_time=240, num_search_workers=2)
```

Assigns named resources to days and shifts, minimizing total scheduled hours
while respecting the configured rules and rewarding preferences.

**Parameters**

- **num_days** (`int`) — days to schedule.
- **resources** (`list[str]`) — unique resource names.
- **shifts** (`list[str]`) — shift names.
- **shifts_hours** (`list`) — duration of each shift (same order as `shifts`).
- **min_working_hours** (`int`) — minimum hours per resource over the horizon.
- **banned_shifts** (`list[dict]`) — `{"resource", "shift", "day"}` entries that
  forbid an assignment. May be `None`.
- **max_resting** (`int`) — maximum resting days per resource; must be
  `< num_days`.
- **required_resources** (`dict`) — `{shift_name: [per-day requirement, …]}`,
  one entry per day for every shift.
- **non_sequential_shifts** (`list[dict]`, optional) —
  `{"origin", "destination"}` pairs that cannot occur on consecutive days.
- **resources_preferences** (`list[dict]`, optional) — `{"resource", "shift"}`
  preferred assignments.
- **resources_prioritization** (`list[dict]`, optional) —
  `{"resource", "weight"}` relative preference weights.
- **max_search_time** (`float`) — solver time limit, seconds.
- **num_search_workers** (`int`) — solver worker threads.

**Validation** — raises `ValueError` when `resources` are not unique, `shifts`
and `shifts_hours` differ in length, `required_resources` is missing a shift or
has the wrong number of days, or `max_resting >= num_days`.

## `solve()`

Returns a `dict` (also stored as `solution_`) with:

- **status**, **cost**, **shifted_hours**, **total_resources**,
  **total_shifts**, **resting_days**;
- **resource_shifts** — list of `{"resource", "day", "shift"}`;
- **resting_resource** — list of `{"resource", "day"}`.

See the [rostering guide](/guide/rostering).
