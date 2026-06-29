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

## Common pitfalls

- `required_resources` is per shift and per day, not per period.
- `resources` must be unique. Use stable identifiers if names can repeat.
- `max_resting` must be smaller than `num_days`.
- Preferences are soft incentives; `banned_shifts` and
  `non_sequential_shifts` are hard constraints.
- If the model is infeasible, first reduce requirements or relax hard
  constraints before tuning preference weights.
