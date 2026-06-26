
[![Tests](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml/badge.svg?branch=main)](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml)
[![Codecov](https://codecov.io/gh/rodrigo-arenas/pyworkforce/branch/main/graphs/badge.svg?branch=main&service=github)](https://codecov.io/github/rodrigo-arenas/pyworkforce?branch=main)
[![PyPI Version](https://badge.fury.io/py/pyworkforce.svg)](https://badge.fury.io/py/pyworkforce)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads/)


# pyworkforce
Tools for workforce management problems such as queue staffing, shift scheduling,
rostering, and operations research optimization. It is geared toward call /
contact centers, but the same techniques apply to hospitals, retail, logistics,
network capacity planning and any operation that has to match a variable demand
with a finite number of resources.

📖 **Full documentation and tutorials:**
[rodrigo-arenas.github.io/pyworkforce](https://rodrigo-arenas.github.io/pyworkforce/)

## Installation

We recommend installing pyworkforce in a virtual environment:

```bash
pip install pyworkforce
```

pyworkforce supports Python 3.12, 3.13, and 3.14.

If you are using Anaconda and run into installation issues, update the environment first:

```bash
conda update --all
```

If the issue is related to OR-Tools, check the
[OR-Tools installation guide](https://github.com/google/or-tools#installation).

For runnable examples, see the
[examples folder](https://github.com/rodrigo-arenas/pyworkforce/tree/main/examples).

## Features

pyworkforce is organized around three planning steps — *how many resources do I
need?* → *how many per shift?* → *who works when?* — plus helpers that tie them
together:

- **Queuing**
  - `ErlangC` — the classic M/M/c queue (infinite patience).
  - `ErlangA` — the M/M/c+M queue with customer **abandonment** (patience),
    computed exactly from the birth–death stationary distribution.
  - `MultiErlangC` / `MultiErlangA` — evaluate many scenarios from a parameter
    grid in parallel, scikit-learn style.
- **Shift coverage helpers** (`pyworkforce.shifts`) — build the `shifts_coverage`
  arrays the schedulers expect from clock hours, spans or explicit periods,
  instead of hand-writing 0/1 arrays.
- **Scheduling** (`pyworkforce.scheduling`) — `MinAbsDifference` and
  `MinRequiredResources` decide how many people to place on each shift, built on
  [OR-Tools](https://developers.google.com/optimization).
- **Rostering** (`pyworkforce.rostering`) — `MinHoursRoster` assigns named people
  to days and shifts while respecting banned shifts, rest days, minimum hours,
  non-sequential shifts and preferences.
- **A scikit-learn-friendly API** — consistent constructors with clear validation
  messages, `get_params()` and readable `repr()` on every estimator, the last
  result stored as `solution_`, and `results_to_dataframe` to turn grid results
  into tidy `pandas` DataFrames.

A brief introduction to the queuing and scheduling ideas can be found in these
posts:
[workforce planning](https://towardsdatascience.com/workforce-planning-optimization-using-python-69af0ef9011a)
and [scheduling](https://towardsdatascience.com/how-to-solve-scheduling-problems-in-python-36a9af8de451).

## Queuing

Estimate how many resources are required to handle incoming work, for example
calls arriving at a call center.

![queue_system](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/erlangc_queue_system.png)

### Erlang C

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, asa=20/60, aht=3, interval=30, shrinkage=0.3)

positions_requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print("positions_requirements: ", positions_requirements)
```
Output:
```
>> positions_requirements:  {'raw_positions': 14,
                             'positions': 20,
                             'service_level': 0.8883500191794669,
                             'occupancy': 0.7142857142857143,
                             'waiting_probability': 0.1741319335950498}
```

### Erlang A (modeling abandonment)

Real customers hang up if they wait too long. `ErlangA` adds a `patience`
parameter and reports the abandonment probability, typically requiring fewer
agents than Erlang C:

```python
from pyworkforce.queuing import ErlangA

erlang = ErlangA(transactions=100, asa=20/60, aht=3, interval=30, patience=5, shrinkage=0.3)

requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85, max_abandonment=0.05)
print("requirements: ", requirements)
```
Output:
```
>> requirements:  {'raw_positions': 13,
                   'positions': 19,
                   'service_level': 0.858...,
                   'occupancy': 0.750...,
                   'abandonment_probability': 0.025...,
                   'waiting_probability': 0.226...,
                   'average_speed_of_answer': 0.125...}
```

### Many scenarios at once

`MultiErlangC` / `MultiErlangA` evaluate a parameter grid in parallel, and
`results_to_dataframe` turns the results into a tidy table:

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

param_grid = {"transactions": [100], "aht": [3], "interval": [30], "asa": [20 / 60], "shrinkage": [0.3]}
multi_erlang = MultiErlangC(param_grid=param_grid, n_jobs=-1)

scenarios = {"service_level": [0.8, 0.85, 0.9], "max_occupancy": [0.8]}
results = multi_erlang.required_positions(scenarios)

df = results_to_dataframe(results, multi_erlang.required_positions_params)
print(df[["service_level", "positions", "service_level_result", "occupancy"]].round(4).to_string(index=False))
```
Output:
```
 service_level  positions  service_level_result  occupancy
          0.80         20                0.8884     0.7143
          0.85         20                0.8884     0.7143
          0.90         22                0.9415     0.6667
```

The input target stays under `service_level`; the achieved value is kept as
`service_level_result`.

## Shift coverage helpers

Describe shifts by their clock hours instead of writing 0/1 arrays. Overnight
shifts wrap past midnight:

```python
from pyworkforce.shifts import shift_coverage_from_hours

shifts_coverage = shift_coverage_from_hours({
    "Morning":   (6, 14),
    "Afternoon": (14, 22),
    "Night":     (22, 6),
}, num_periods=24)
```

The output plugs straight into the schedulers below. See also
`shift_coverage_from_spans`, `shift_coverage_from_periods`,
`validate_shift_coverage` and `coverage_to_dataframe`.

## Scheduling

Given the required resources per period, decide how many people to place on each
predefined shift.

```python
from pyworkforce.scheduling import MinAbsDifference, MinRequiredResources

# Rows are days. Each value is the number of required positions for one hour of the day.
required_resources = [
    [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
    [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
]

# Each shift has 24 entries, one per hour. Use 1 if the shift covers that hour, otherwise 0.
shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                   "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                   "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

# Minimize the absolute difference between required and scheduled resources
difference_scheduler = MinAbsDifference(num_days=2,
                                        periods=24,
                                        shifts_coverage=shifts_coverage,
                                        required_resources=required_resources,
                                        max_period_concurrency=27,
                                        max_shift_concurrency=25)
difference_solution = difference_scheduler.solve()

# Minimize the (optionally weighted) number of scheduled resources while covering every period
requirements_scheduler = MinRequiredResources(num_days=2,
                                              periods=24,
                                              shifts_coverage=shifts_coverage,
                                              required_resources=required_resources,
                                              max_period_concurrency=27,
                                              max_shift_concurrency=25)
requirements_solution = requirements_scheduler.solve()

print("difference_solution :", difference_solution["status"], difference_solution["cost"])
print("requirements_solution :", requirements_solution["status"], requirements_solution["cost"])
```
Output:
```
>> difference_solution: {'status': 'OPTIMAL',
                          'cost': 157.0,
                          'resources_shifts': [{'day': 0, 'shift': 'Morning', 'resources': 8},
                                               {'day': 0, 'shift': 'Afternoon', 'resources': 11},
                                               {'day': 0, 'shift': 'Night', 'resources': 9},
                                               {'day': 0, 'shift': 'Mixed', 'resources': 1},
                                               ... ]}

>> requirements_solution: {'status': 'OPTIMAL',
                           'cost': 113.0,
                           'resources_shifts': [{'day': 0, 'shift': 'Morning', 'resources': 15},
                                                {'day': 0, 'shift': 'Afternoon', 'resources': 13},
                                                ... ]}
```

`MinRequiredResources` also accepts a `cost_dict` to weight shifts differently
(for example, more expensive night shifts).

## Rostering

Assign **named** people to days and shifts while respecting individual rules and
preferences.

```python
from pyworkforce.rostering import MinHoursRoster

roster = MinHoursRoster(
    num_days=2,
    resources=["ana@co", "ben@co", "cara@co", "dan@co", "eve@co"],
    shifts=["Morning", "Night"],
    shifts_hours=[8, 8],
    min_working_hours=8,
    max_resting=1,
    required_resources={"Morning": [2, 2], "Night": [1, 1]},
    banned_shifts=[{"resource": "ana@co", "shift": "Night", "day": 0}],
    resources_preferences=[{"resource": "ana@co", "shift": "Morning"}],
)

solution = roster.solve()
print(solution["status"], solution["resource_shifts"][:2])
```
Output:
```
OPTIMAL [{'resource': 'ana@co', 'day': 0, 'shift': 'Morning'},
         {'resource': 'ana@co', 'day': 1, 'shift': 'Morning'}]
```

`ana@co` is given her preferred `Morning` shift and never `Night` on day 0,
exactly as configured.

## Documentation and tutorials

The [documentation site](https://rodrigo-arenas.github.io/pyworkforce/) includes
narrative guides, a full API reference, and self-contained, notebook-style
tutorials with real outputs:

- [End-to-end planning](https://rodrigo-arenas.github.io/pyworkforce/guide/end-to-end)
  — demand → required positions → shift coverage → schedule → roster.
- [Comparing scenarios](https://rodrigo-arenas.github.io/pyworkforce/guide/scenarios)
  — grids and DataFrames.

## Contributing

Contributions are very welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the
local development setup, how to run the tests and linter, and the pull-request
workflow.

## License

pyworkforce is released under the [MIT License](LICENSE).
