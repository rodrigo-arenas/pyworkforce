# Recipes

Recipes are short, task-oriented snippets for common workforce planning jobs.
Use tutorials when you want a complete workflow; use recipes when you need one
practical move to copy into a notebook or pipeline.

## Queue staffing

### How many agents do I need for 80/20 service level?

Use Erlang C when callers wait and you are not modeling abandonment.

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, aht=3, asa=20 / 60, interval=30, shrinkage=0.3)
result = erlang.required_positions(service_level=0.80, max_occupancy=0.85)

print(result["positions"])
```

```text
20
```

`positions` includes shrinkage. Use `raw_positions` when you need productive
seats before shrinkage.

### Compare service levels across shrinkage assumptions

Use a `Multi*` estimator when you want a scenario table.

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

param_grid = {
    "transactions": [100],
    "aht": [3],
    "asa": [20 / 60],
    "interval": [30],
    "shrinkage": [0.20, 0.30, 0.40],
}

multi = MultiErlangC(param_grid=param_grid, n_jobs=-1)
results = multi.required_positions({"service_level": [0.80], "max_occupancy": [0.85]})
df = results_to_dataframe(results, multi.required_positions_params)

print(df[["shrinkage", "raw_positions", "positions", "occupancy"]].to_string(index=False))
```

### Size SIP trunks with Erlang B

Use Erlang B for pure-loss systems where blocked calls are cleared, not queued.

```python
from pyworkforce.queuing import ErlangB

trunks = ErlangB(transactions=100, aht=3, interval=30)
print(trunks.required_positions(max_blocking=0.02)["raw_positions"])
```

```text
17
```

## Shift coverage and scheduling

### Convert shift start/end hours into coverage arrays

```python
from pyworkforce.shifts import coverage_to_dataframe, shift_coverage_from_hours

coverage = shift_coverage_from_hours(
    {"Early": (6, 14), "Late": (14, 22), "Night": (22, 6)},
    num_periods=24,
)

print(coverage_to_dataframe(coverage).loc[["Early", "Night"], [0, 6, 13, 22]].to_string())
```

### Export scheduled shift counts to a pandas DataFrame

The solver returns a list of dictionaries, so pandas can consume it directly.

```python
import pandas as pd

from pyworkforce.scheduling import MinRequiredResources
from pyworkforce.shifts import shift_coverage_from_hours

coverage = shift_coverage_from_hours({"Day": (8, 16), "Evening": (16, 24)}, num_periods=24)
required = [[0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2]]

solver = MinRequiredResources(
    num_days=1,
    periods=24,
    shifts_coverage=coverage,
    required_resources=required,
    max_period_concurrency=10,
    max_shift_concurrency=10,
)

solution = solver.solve()
df = pd.DataFrame(solution["resources_shifts"])
print(df.to_string(index=False))
```

## Rostering

### Avoid assigning a person to a banned shift

Use `banned_shifts` for hard exclusions such as availability, certification, or
labor-rule constraints.

```python
from pyworkforce.rostering import MinHoursRoster

roster = MinHoursRoster(
    num_days=2,
    resources=["ana", "ben", "cara"],
    shifts=["Morning", "Night"],
    shifts_hours=[8, 8],
    min_working_hours=8,
    max_resting=1,
    required_resources={"Morning": [1, 1], "Night": [1, 1]},
    banned_shifts=[{"resource": "ana", "shift": "Night", "day": 0}],
)

solution = roster.solve()
print(any(x == {"resource": "ana", "day": 0, "shift": "Night"} for x in solution["resource_shifts"]))
```

```text
False
```

## Break scheduling

### Schedule lunch breaks without dropping below coverage

Set `min_coverage` to the minimum number of agents that must remain available
in each period.

```python
from pyworkforce.breaks import BreakScheduler

scheduler = BreakScheduler(
    num_days=1,
    periods=8,
    shifts_coverage={"Day": [1, 1, 1, 1, 1, 1, 1, 1]},
    scheduled_resources={"Day": [3]},
    breaks=[{"name": "Lunch", "duration_periods": 2, "min_start_after": 1, "max_end_before": 1}],
    min_coverage=[[2, 2, 2, 2, 2, 2, 2, 2]],
)

result = scheduler.solve()
print(result["status"])
print(result["break_schedule"][0])
```

```text
OPTIMAL
{'shift': 'Day', 'day': 0, 'slot': 0, 'break_name': 'Lunch', 'start_period': 3, 'end_period': 5}
```

## Common pitfalls

- Keep time units consistent. If `aht` is in minutes, `asa`, `interval`, and
  `patience` should be in minutes too.
- Use Erlang A, not Erlang C, when abandonment materially affects staffing.
- Give scheduling solvers realistic upper bounds in `max_period_concurrency`
  and `max_shift_concurrency`; bounds that are too low make feasible plans look
  infeasible.
- Validate labor-policy assumptions before operational use. pyworkforce solves
  the model you give it; it does not know your contracts, regulations, or local
  operating rules unless you encode them.
