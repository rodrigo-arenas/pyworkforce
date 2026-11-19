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
        "min_start_after": 1,   # must start at least 1 period into the shift
        "max_end_before": 1,    # must end at least 1 period before the shift ends
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
print("Scheduled breaks:", len(result["break_schedule"]))
```

```text
OPTIMAL
Scheduled breaks: 5
```

## Connecting to the scheduling output

Call `scheduled_resources()` on a solved shift plan to get the mapping expected
by `BreakScheduler`. The next example reuses the shift definitions and break
windows above. It schedules one extra person per period beyond `min_coverage`
to leave room for breaks.

```python
from pyworkforce.scheduling import MinRequiredResources

shift_plan = MinRequiredResources(
    num_days=1,
    periods=16,
    shifts_coverage=shifts_coverage,
    required_resources=[[3] * 8 + [2] * 8],
    max_period_concurrency=3,
    max_shift_concurrency=3,
)
shift_plan.solve()

break_sched = BreakScheduler(
    num_days=1,
    periods=16,
    shifts_coverage=shifts_coverage,
    scheduled_resources=shift_plan.scheduled_resources(),
    breaks=breaks,
    min_coverage=min_coverage,
)
print(break_sched.solve()["status"])
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

## Common pitfalls

- `BreakScheduler` assigns breaks to shift slots, not named employees.
- `min_coverage` is the number of agents that must remain available, not the
  number allowed to go on break.
- Break windows are relative to the shift, not absolute clock periods.
- If every slot must take a long break inside a narrow window, the problem may
  be infeasible unless there is enough coverage slack.
