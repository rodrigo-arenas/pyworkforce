# Break scheduling

After the [scheduling step](/guide/scheduling) you know how many agents work
each shift and day. The **`BreakScheduler`** takes that result and assigns a
start time to every break for every agent slot, while guaranteeing that the
number of agents simultaneously on break never drops coverage below your
required minimum.

## How it fits in the planning flow

```
Queue staffing  →  Shift scheduling  →  Rostering  →  Break scheduling
 (ErlangC/A)       (MinAbsDifference/      (MinHours-      (BreakScheduler)
                    MinRequiredResources)    Roster)
```

`BreakScheduler` works at the **slot level**, not the named-agent level: it
assigns breaks to agent slot 0, slot 1, … for each shift/day combination.
You can run it immediately after the scheduling step, before or after rostering.

## Minimal example

```python
from pyworkforce.breaks import BreakScheduler

# Two 8-period shifts running on 1 day; three agents on Morning, two on Afternoon
shifts_coverage = {
    "Morning":   [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
}
scheduled_resources = {"Morning": [3], "Afternoon": [2]}

breaks = [
    {
        "name": "Lunch",
        "duration_periods": 2,
        "min_start_after": 2,   # must start at least 2 periods into the shift
        "max_end_before": 2,    # must end at least 2 periods before the shift ends
    }
]

# At every period at least this many agents must NOT be on break
min_coverage = [[2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1]]

scheduler = BreakScheduler(
    num_days=1,
    periods=16,
    shifts_coverage=shifts_coverage,
    scheduled_resources=scheduled_resources,
    breaks=breaks,
    min_coverage=min_coverage,
)

result = scheduler.solve()
print(result["status"])
for entry in result["break_schedule"]:
    print(entry)
```

```text
OPTIMAL
{'shift': 'Morning', 'day': 0, 'slot': 0, 'break_name': 'Lunch', 'start_period': 2, 'end_period': 4}
{'shift': 'Morning', 'day': 0, 'slot': 1, 'break_name': 'Lunch', 'start_period': 4, 'end_period': 6}
{'shift': 'Morning', 'day': 0, 'slot': 2, 'break_name': 'Lunch', 'start_period': 2, 'end_period': 4}
{'shift': 'Afternoon', 'day': 0, 'slot': 0, 'break_name': 'Lunch', 'start_period': 10, 'end_period': 12}
{'shift': 'Afternoon', 'day': 0, 'slot': 1, 'break_name': 'Lunch', 'start_period': 12, 'end_period': 14}
```

## Connecting to the scheduling output

Pass the `resources_shifts` output of a scheduler directly into
`scheduled_resources`:

```python
from pyworkforce.scheduling import MinRequiredResources

sched_result = scheduler_obj.solve()

# Build scheduled_resources from the solver output
scheduled_resources = {}
for entry in sched_result["resources_shifts"]:
    shift = entry["shift"]
    day   = entry["day"]
    count = entry["resources"]
    if shift not in scheduled_resources:
        scheduled_resources[shift] = [0] * num_days
    scheduled_resources[shift][day] = count

break_sched = BreakScheduler(
    num_days=num_days,
    periods=periods,
    shifts_coverage=shifts_coverage,
    scheduled_resources=scheduled_resources,
    breaks=breaks,
    min_coverage=required_resources,  # reuse the same requirements array
)
```

## Defining breaks

Each element of the `breaks` list is a dict with:

| Key | Type | Description |
| --- | --- | --- |
| `name` | `str` | Unique identifier for this break type |
| `duration_periods` | `int` | Length of the break in periods |
| `min_start_after` | `int` | Periods into the shift before the break may start (default `0`) |
| `max_end_before` | `int` | Periods remaining in the shift after the break must end (default `0`) |

You can define multiple break types (for example a short rest and a meal break):

```python
breaks = [
    {"name": "Rest",  "duration_periods": 1, "min_start_after": 1, "max_end_before": 1},
    {"name": "Lunch", "duration_periods": 2, "min_start_after": 3, "max_end_before": 2},
]
```

The solver will ensure that two breaks assigned to the same agent slot cannot
overlap.

## Solver output

`solve()` returns a dict:

| Key | Type | Description |
| --- | --- | --- |
| `status` | `str` | `"OPTIMAL"`, `"FEASIBLE"`, or `"INFEASIBLE"` |
| `cost` | `float` | Objective value (`0.0` for feasible / optimal; `−1` when infeasible) |
| `break_schedule` | `list[dict]` | One entry per `(shift, day, slot, break)` |

Each `break_schedule` entry has:

| Key | Description |
| --- | --- |
| `shift` | Shift name |
| `day` | Day index (0-based) |
| `slot` | Agent slot index (0-based within that shift/day) |
| `break_name` | Name from the `breaks` definition |
| `start_period` | Start period (inclusive) |
| `end_period` | End period (exclusive: `start_period + duration_periods`) |

## Coverage guarantee

The solver enforces that at every period the number of agents **on break** is at
most `total_scheduled − min_coverage`. If no feasible assignment exists — for
example because `min_coverage` is set too high — the result status is
`"INFEASIBLE"`.

::: tip Setting min_coverage
A simple rule of thumb: pass the same `required_resources` array you used in
the scheduling step. This ensures you never send so many agents on break that
service levels drop below what was planned.
:::
