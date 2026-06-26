# Quick Start

This page shows one small example from each module. Each snippet is
self-contained and runnable.

## Staffing a queue (Erlang C)

How many agents handle 100 calls in a 30-minute interval, with a 3-minute
average handle time, answering 80% of calls within 20 seconds?

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, asa=20 / 60, aht=3, interval=30, shrinkage=0.3)

requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print(requirements)
```

```text
{'raw_positions': 14,
 'positions': 20,
 'service_level': 0.8883500191794669,
 'occupancy': 0.7142857142857143,
 'waiting_probability': 0.1741319335950498}
```

`raw_positions` are the productive agents needed; `positions` adds the
shrinkage allowance (breaks, training, etc.).

## Modeling abandonment (Erlang A)

Real customers hang up. With an average patience of 5 minutes, fewer agents are
needed because some callers leave the queue:

```python
from pyworkforce.queuing import ErlangA

erlang = ErlangA(transactions=100, aht=3, asa=20 / 60,
                 interval=30, patience=5, shrinkage=0.3)

print(erlang.required_positions(service_level=0.8,
                                max_occupancy=0.85,
                                max_abandonment=0.05))
```

```text
{'raw_positions': 13,
 'positions': 19,
 'service_level': 0.858...,
 'occupancy': 0.750...,
 'abandonment_probability': 0.025...,
 'waiting_probability': 0.226...,
 'average_speed_of_answer': 0.125...}
```

## Building shift coverage

Describe shifts by their clock hours instead of writing 0/1 arrays:

```python
from pyworkforce.shifts import shift_coverage_from_hours

shifts_coverage = shift_coverage_from_hours({
    "Morning":   (6, 14),
    "Afternoon": (14, 22),
    "Night":     (22, 6),   # overnight, wraps past midnight
}, num_periods=24)
```

## Scheduling people onto shifts

```python
from pyworkforce.scheduling import MinRequiredResources

# Required resources per hour, one row per day.
required_resources = [
    [3, 3, 3, 3, 3, 3, 6, 6, 6, 6, 8, 8, 8, 8, 6, 6, 6, 6, 4, 4, 4, 4, 3, 3],
    [4, 4, 4, 4, 4, 4, 7, 7, 7, 7, 9, 9, 9, 9, 7, 7, 7, 7, 5, 5, 5, 5, 4, 4],
]

scheduler = MinRequiredResources(
    num_days=2,
    periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=30,
    max_shift_concurrency=30,
)

solution = scheduler.solve()
print(solution["status"], solution["cost"])
```

## Rostering named people

```python
from pyworkforce.rostering import MinHoursRoster

roster = MinHoursRoster(
    num_days=2,
    resources=["a@co", "b@co", "c@co"],
    shifts=["Morning", "Night"],
    shifts_hours=[8, 8],
    min_working_hours=8,
    banned_shifts=[{"resource": "a@co", "shift": "Night", "day": 0}],
    max_resting=1,
    required_resources={"Morning": [1, 1], "Night": [1, 1]},
)

solution = roster.solve()
print(solution["status"])
```

Next, read the [Erlang C guide](/guide/erlangc) for the theory and a deeper
walkthrough.
