# Rostering

Rostering is the final planning step: assign **named** resources (specific
people) to days and shifts, respecting individual rules and preferences.

`MinHoursRoster` builds a resource-level roster that covers the shift
requirements with the **minimum scheduled hours**, optionally rewarding shift
preferences.

## Inputs

| Argument | Description |
| --- | --- |
| `num_days` | Number of days to schedule |
| `resources` | List of unique resource names |
| `shifts` | List of shift names |
| `shifts_hours` | Duration of each shift (same order as `shifts`) |
| `min_working_hours` | Minimum hours per resource over the horizon |
| `max_resting` | Maximum resting days per resource (must be `< num_days`) |
| `required_resources` | `{shift_name: [per-day requirement, …]}` |
| `banned_shifts` | Shifts a resource cannot work on a given day |
| `non_sequential_shifts` | Shift pairs that cannot follow one another |
| `resources_preferences` | Preferred shifts per resource |
| `resources_prioritization` | Relative weight of each resource's preferences |
| `shift_block_starts` | Optional day indices at which each person may start a different shift type |

::: tip Validation
`MinHoursRoster` checks its inputs up front: `resources` must be unique,
`shifts` and `shifts_hours` must have the same length, `required_resources`
must contain every shift with one entry per day, and `max_resting` must be
smaller than `num_days`. Each failure raises a clear `ValueError`.
:::

## Example

```python
from pyworkforce.rostering import MinHoursRoster

roster = MinHoursRoster(
    num_days=2,
    resources=["e.johnston@co", "m.lee@co", "a.smith@co"],
    shifts=["Morning", "Night"],
    shifts_hours=[8, 8],
    min_working_hours=8,
    max_resting=1,
    required_resources={"Morning": [1, 1], "Night": [1, 1]},
    banned_shifts=[{"resource": "e.johnston@co", "shift": "Night", "day": 0}],
    non_sequential_shifts=[{"origin": "Night", "destination": "Morning"}],
    resources_preferences=[{"resource": "m.lee@co", "shift": "Morning"}],
    resources_prioritization=[{"resource": "m.lee@co", "weight": 2}],
)

solution = roster.solve()
print(solution["status"])
```

## The solution

`solve()` returns a dictionary (also stored as `solution_`) describing both who
works and who rests:

```python
{
  "status": "OPTIMAL",
  "cost": ...,
  "shifted_hours": ...,
  "total_resources": 3,
  "total_shifts": ...,
  "resting_days": ...,
  "resource_shifts": [{"resource": "m.lee@co", "day": 0, "shift": "Morning"}, ...],
  "resting_resource": [{"resource": "a.smith@co", "day": 1}, ...],
}
```

## Rules in detail

- **`banned_shifts`** — each entry
  `{"resource": ..., "shift": ..., "day": ...}` forbids that exact assignment.
- **`non_sequential_shifts`** — each entry
  `{"origin": ..., "destination": ...}` prevents `destination` from being
  worked the day after `origin` (e.g. no Morning right after a Night).
- **`resources_preferences`** — each entry `{"resource": ..., "shift": ...}`
  marks a preferred shift; preferences reduce the effective cost of those
  assignments.
- **`resources_prioritization`** — each entry `{"resource": ..., "weight": ...}`
  scales how strongly a resource's preferences are honored.

## Keep the same shift through a day off

A worker on the early shift may need a predictable start time when returning
from a day off. Pass `shift_block_starts=[0, 7]` for a ten-day plan to keep each
person on one shift during days 0–6 and one during days 7–9. At a boundary the
shift can stay the same or change. A block may also be entirely off.

You choose the boundaries. Use `range(0, num_days, 7)` for seven-day blocks
beginning on the first day of your plan. If the first block has three days
before the next local week begins, use starts such as `[0, 3, 10]` for a
fourteen-day horizon. Day 0 can correspond to any calendar date.

In the example, both shifts need one person each working day. Everyone has day
3 off. Operator A is unavailable for Late on day 0 and Early on day 7. Those
two availability limits and the block rule determine the assignments.

```python
from pyworkforce.rostering import MinHoursRoster

resources = ["Operator A", "Operator B"]
demand = [1, 1, 1, 0, 1, 1, 1, 1, 1, 1]
roster = MinHoursRoster(
    num_days=10,
    resources=resources,
    shifts=["Early", "Late"],
    shifts_hours=[8, 8],
    min_working_hours=72,
    max_resting=1,
    required_resources={"Early": demand, "Late": demand},
    banned_shifts=[
        {"resource": "Operator A", "shift": "Late", "day": 0},
        {"resource": "Operator A", "shift": "Early", "day": 7},
    ],
    shift_block_starts=[0, 7],
)

solution = roster.solve()
if solution["status"] not in {"FEASIBLE", "OPTIMAL"}:
    raise RuntimeError(solution["status"])
assignments = {(item["resource"], item["day"]): item["shift"] for item in solution["resource_shifts"]}
for person in resources:
    days = [assignments.get((person, day), "Off") for day in range(roster.num_days)]
    print(f"{person} | {' '.join(days[:7])} | {' '.join(days[7:])}")
```

```text
Operator A | Early Early Early Off Early Early Early | Late Late Late
Operator B | Late Late Late Off Late Late Late | Early Early Early
```

Run `python examples/rostering/shift_blocks.py` from an installed development
checkout to reproduce the roster. The daily staffing requirements still apply,
and forbidden next-day transitions still apply across block boundaries.
`max_resting` caps total days off per person over the whole plan. Weekly rest
entitlements or rotating weekends require separate rules.

## Common pitfalls

- `required_resources` is per shift and per day, not per period.
- `resources` must be unique. Use stable identifiers if names can repeat.
- `max_resting` must be smaller than `num_days`.
- Preferences are soft incentives; `banned_shifts` and
  `non_sequential_shifts` are hard constraints.
- If the model is infeasible, first reduce requirements or relax hard
  constraints before tuning preference weights.
