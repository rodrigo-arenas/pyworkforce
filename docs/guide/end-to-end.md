# Tutorial: planning a contact center day, end to end

This tutorial walks through the three pyworkforce planning steps on a single,
self-contained example: from raw call volumes to a named roster. Every code
block is runnable top to bottom, and the outputs shown are the **real** outputs
produced by the snippets.

We will:

1. turn hourly call volumes into the **positions required per hour** (queuing);
2. describe our **shifts** as coverage arrays;
3. **schedule** how many people go on each shift;
4. **roster** named agents onto days and shifts.

## Step 1 — required positions per hour

We start from a forecast of calls per hour for one day, then size each hour
with [Erlang C](/guide/erlangc). We also size it with
[Erlang A](/guide/erlanga) (which models abandonment) to compare.

```python
from pyworkforce.queuing import ErlangC, ErlangA

calls_per_hour = [
    12, 8, 6, 5, 5, 8, 20, 45, 70, 85, 90, 88,
    80, 78, 82, 80, 70, 60, 48, 40, 32, 26, 20, 15,
]

required_c, required_a = [], []
for calls in calls_per_hour:
    c = ErlangC(transactions=calls, aht=4, asa=20 / 60, interval=60, shrinkage=0.3)
    required_c.append(c.required_positions(service_level=0.8, max_occupancy=0.85)["positions"])
    a = ErlangA(transactions=calls, aht=4, asa=20 / 60, interval=60, patience=8, shrinkage=0.3)
    required_a.append(a.required_positions(service_level=0.8, max_occupancy=0.85)["positions"])

print("Erlang C:", required_c)
print("Erlang A:", required_a)
print("Total agent-hours  C:", sum(required_c), " A:", sum(required_a))
```

```text
Erlang C: [5, 3, 3, 3, 3, 3, 5, 8, 12, 13, 13, 13, 12, 12, 12, 12, 12, 10, 9, 8, 6, 6, 5, 5]
Erlang A: [3, 3, 3, 3, 3, 3, 5, 8, 10, 12, 13, 13, 12, 12, 12, 12, 10, 9, 8, 8, 6, 6, 5, 5]
Total agent-hours  C: 193  A: 184
```

Because some callers abandon the queue, Erlang A asks for slightly fewer
agent-hours. We'll use the (more conservative) Erlang C numbers below.

## Step 2 — describe the shifts

Instead of hand-writing 0/1 arrays, build the coverage from clock hours with
the [shift helpers](/guide/shifts). The `Night` shift wraps past midnight.

```python
from pyworkforce.shifts import shift_coverage_from_hours, coverage_to_dataframe

shifts_coverage = shift_coverage_from_hours({
    "Early": (6, 14),
    "Day":   (9, 17),
    "Late":  (13, 21),
    "Night": (21, 6),
}, num_periods=24)

print(coverage_to_dataframe(shifts_coverage).to_string())
```

```text
       0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23
Early   0   0   0   0   0   0   1   1   1   1   1   1   1   1   0   0   0   0   0   0   0   0   0   0
Day     0   0   0   0   0   0   0   0   0   1   1   1   1   1   1   1   1   0   0   0   0   0   0   0
Late    0   0   0   0   0   0   0   0   0   0   0   0   0   1   1   1   1   1   1   1   1   0   0   0
Night   1   1   1   1   1   1   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1   1   1
```

## Step 3 — schedule people onto shifts

Now decide how many people to place on each shift so every hour is covered,
using [`MinRequiredResources`](/guide/scheduling). The required resources are
the per-hour positions from Step 1 (one row per day).

```python
from pyworkforce.scheduling import MinRequiredResources

scheduler = MinRequiredResources(
    num_days=1, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=[required_c],
    max_period_concurrency=40, max_shift_concurrency=30,
)

schedule = scheduler.solve()
print("status:", schedule["status"], "| total agents (cost):", schedule["cost"])
for item in schedule["resources_shifts"]:
    print(item)
```

```text
status: OPTIMAL | total agents (cost): 30.0
{'day': 0, 'shift': 'Early', 'resources': 12}
{'day': 0, 'shift': 'Day', 'resources': 1}
{'day': 0, 'shift': 'Late', 'resources': 11}
{'day': 0, 'shift': 'Night', 'resources': 6}
```

The solver staffs 30 agents across the four shifts and covers every hour.

::: tip
`max_period_concurrency` and `max_shift_concurrency` are **upper bounds**. If
they are too small the problem becomes `INFEASIBLE`; give them enough head-room
for the hours where shifts overlap.
:::

## Step 4 — roster named agents

Finally, assign **named** people to days and shifts with
[`MinHoursRoster`](/guide/rostering). To keep the output readable, here is a
small, self-contained roster (in practice you would feed the per-shift counts
from Step 3). Note the banned shift and the preference being respected.

```python
from pyworkforce.rostering import MinHoursRoster

roster = MinHoursRoster(
    num_days=2,
    resources=["ana@co", "ben@co", "cara@co", "dan@co", "eve@co", "finn@co", "gil@co"],
    shifts=["Early", "Late", "Night"],
    shifts_hours=[8, 8, 9],
    min_working_hours=8,
    max_resting=1,
    required_resources={"Early": [2, 2], "Late": [2, 2], "Night": [1, 1]},
    banned_shifts=[{"resource": "ana@co", "shift": "Night", "day": 0}],
    resources_preferences=[{"resource": "ana@co", "shift": "Early"}],
)

sol = roster.solve()
print("status:", sol["status"], "| shifted_hours:", sol["shifted_hours"],
      "| resting_days:", sol["resting_days"])
for a in sol["resource_shifts"]:
    print(a)
```

```text
status: OPTIMAL | shifted_hours: 82 | resting_days: 4
{'resource': 'ana@co', 'day': 0, 'shift': 'Early'}
{'resource': 'ana@co', 'day': 1, 'shift': 'Early'}
{'resource': 'ben@co', 'day': 1, 'shift': 'Night'}
{'resource': 'cara@co', 'day': 0, 'shift': 'Early'}
{'resource': 'cara@co', 'day': 1, 'shift': 'Early'}
{'resource': 'dan@co', 'day': 0, 'shift': 'Late'}
{'resource': 'eve@co', 'day': 0, 'shift': 'Late'}
{'resource': 'finn@co', 'day': 0, 'shift': 'Night'}
{'resource': 'finn@co', 'day': 1, 'shift': 'Late'}
{'resource': 'gil@co', 'day': 1, 'shift': 'Late'}
```

`ana@co` is given her preferred `Early` shift and is never assigned `Night` on
day 0, exactly as configured.

## Recap

In a few dozen lines you went from a demand forecast to a concrete, named
roster:

- **queuing** turned demand into required positions per hour;
- **shift helpers** described the shifts without hand-written arrays;
- **scheduling** chose how many people per shift;
- **rostering** assigned named people while honoring rules and preferences.

From here, explore running [many scenarios at once](/guide/scenarios) to
compare service-level targets, patience assumptions and more.
