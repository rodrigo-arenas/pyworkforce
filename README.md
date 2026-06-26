[![Tests](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml/badge.svg?branch=main)](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml)
[![Codecov](https://codecov.io/gh/rodrigo-arenas/pyworkforce/branch/main/graphs/badge.svg?branch=main&service=github)](https://codecov.io/github/rodrigo-arenas/pyworkforce?branch=main)
[![PyPI Version](https://badge.fury.io/py/pyworkforce.svg)](https://badge.fury.io/py/pyworkforce)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-rodrigo--arenas.github.io-blue)](https://rodrigo-arenas.github.io/pyworkforce/stable/)

# pyworkforce

**Workforce management, made practical.** Covers the full planning pipeline from
queue staffing to named rosters and break scheduling — built on Erlang queuing
theory and OR-Tools constraint programming, with a scikit-learn-style API.

> Geared toward contact / call centres, but the same techniques apply to
> hospitals, retail, logistics and any operation matching variable demand to
> finite resources.

📖 **Full documentation:** [rodrigo-arenas.github.io/pyworkforce](https://rodrigo-arenas.github.io/pyworkforce/stable/)

---

## Installation

```bash
pip install pyworkforce
```

```bash
conda install -c conda-forge pyworkforce   # via conda-forge
```

Requires Python 3.12 – 3.14.

---

## The planning workflow

pyworkforce covers five sequential planning steps:

![Planning workflow](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/planning_pipeline.svg)

| Step | Module | Key classes | Question answered |
|------|--------|-------------|-------------------|
| 1 | `pyworkforce.queuing` | `ErlangC`, `ErlangA`, `ErlangB` | How many agents / channels are needed? |
| 2 | `pyworkforce.staffing` | `MultiSkillStaffing` | What is the optimal skill-profile mix? |
| 3 | `pyworkforce.scheduling` | `MinRequiredResources`, `MinAbsDifference` | How many agents per shift? |
| 4 | `pyworkforce.rostering` | `MinHoursRoster` | Who works on which day and shift? |
| 5 | `pyworkforce.breaks` | `BreakScheduler` | When do individual breaks happen? |

---

## 1 — Queuing

Estimate the number of agents (or channels) needed to meet a service target given
an incoming demand.

### Erlang C — infinite patience

The classic M/M/c queue: Poisson arrivals, exponential handling times, unlimited
waiting room.

![Erlang C queue system](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/erlangc_queue_system.svg)

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, aht=3, asa=20/60, interval=30, shrinkage=0.3)

result = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print(result)
```

```
{'raw_positions': 14,
 'positions': 20,
 'service_level': 0.8884,
 'occupancy': 0.7143,
 'waiting_probability': 0.1741}
```

### Erlang A — finite patience (abandonment)

Adds a `patience` parameter: callers who wait too long hang up.
Typically requires fewer agents than Erlang C.

![Erlang A queue system — with abandonment](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/erlanga_queue_system.svg)

```python
from pyworkforce.queuing import ErlangA

erlang = ErlangA(transactions=100, aht=3, asa=20/60, interval=30,
                 patience=5, shrinkage=0.3)

result = erlang.required_positions(service_level=0.8, max_occupancy=0.85,
                                   max_abandonment=0.05)
print(result)
```

```
{'raw_positions': 13,
 'positions': 19,
 'service_level': 0.8584,
 'occupancy': 0.7500,
 'abandonment_probability': 0.0253,
 'waiting_probability': 0.2265,
 'average_speed_of_answer': 0.1258}
```

### Erlang B — pure loss (no waiting room)

M/M/c/c queue: blocked calls are shed immediately.
Use this for SIP trunk sizing, IVR channel capacity and overflow links.

![Erlang B loss system](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/erlangb_loss_system.svg)

```python
from pyworkforce.queuing import ErlangB

erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)

result = erlang.required_positions(max_blocking=0.02)
print(result)
```

```
{'raw_positions': 17,
 'positions': 25,
 'blocking_probability': 0.0183,
 'occupancy': 0.9375}
```

### Running many scenarios at once

`MultiErlangC`, `MultiErlangA` and `MultiErlangB` sweep a parameter grid in
parallel (scikit-learn style) and `results_to_dataframe` turns the output into a
tidy table:

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

param_grid = {"transactions": [100], "aht": [3], "interval": [30],
              "asa": [20/60], "shrinkage": [0.3]}
multi = MultiErlangC(param_grid=param_grid, n_jobs=-1)

results = multi.required_positions({"service_level": [0.80, 0.85, 0.90],
                                    "max_occupancy": [0.85]})

df = results_to_dataframe(results, multi.required_positions_params)
print(df[["service_level", "positions", "occupancy"]].round(4).to_string(index=False))
```

```
 service_level  positions  occupancy
          0.80         20     0.7143
          0.85         20     0.7143
          0.90         22     0.6667
```

---

## 2 — Multi-skill staffing

When agents handle multiple contact types (e.g. English, Billing, Technical),
`MultiSkillStaffing` finds the cheapest mix of skill profiles that meets every
skill's coverage requirement. Flexible (multi-skilled) agents count towards all
skills they hold.

```python
from pyworkforce.staffing import MultiSkillStaffing

skills   = ["Billing", "Technical"]
profiles = [
    {"name": "Billing_only",   "skills": ["Billing"],              "cost": 1.0},
    {"name": "Technical_only", "skills": ["Technical"],            "cost": 1.0},
    {"name": "Flexible",       "skills": ["Billing", "Technical"], "cost": 1.5},
]
required = {"Billing": 5, "Technical": 3}

ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
result = ms.solve()

print(f"status={result['status']}  total={result['total_agents']}  cost={result['cost']}")
for entry in result["agents_per_profile"]:
    print(f"  {entry['profile']:18s}: {entry['agents']}")
```

```
status=OPTIMAL  total=5  cost=6.5
  Billing_only      : 2
  Technical_only    : 0
  Flexible          : 3
```

3 flexible + 2 billing-only = cost 6.5, vs 8.0 for pure dedicated agents.

---

## 3 — Shift coverage helpers

Build the `shifts_coverage` arrays the schedulers expect from clock hours instead
of writing 0/1 arrays by hand:

```python
from pyworkforce.shifts import shift_coverage_from_hours

shifts_coverage = shift_coverage_from_hours({
    "Morning":   (6, 14),
    "Afternoon": (14, 22),
    "Night":     (22, 6),   # wraps past midnight
}, num_periods=24)
```

See also `shift_coverage_from_spans`, `shift_coverage_from_periods`,
`validate_shift_coverage` and `coverage_to_dataframe`.

---

## 4 — Scheduling

Given the required resources per period, decide how many agents to place on each
shift using constraint programming (OR-Tools):

```python
from pyworkforce.scheduling import MinRequiredResources

# One row per day; each value = required agents for that hour
required_resources = [
    [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
    [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8],
]
shifts_coverage = {
    "Morning":   [0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    "Afternoon": [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    "Night":     [1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1],
    "Mixed":     [0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0],
}

scheduler = MinRequiredResources(
    num_days=2, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=27, max_shift_concurrency=25,
)
solution = scheduler.solve()
print(solution["status"], solution["cost"])
```

```
OPTIMAL 113.0
```

`MinAbsDifference` minimises the absolute difference between required and
scheduled; `MinRequiredResources` minimises total agents (optionally weighted by
shift cost).

---

## 5 — Rostering

Assign **named** people to days and shifts while respecting individual rules:

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
print(solution["status"])
for a in solution["resource_shifts"][:3]:
    print(a)
```

```
OPTIMAL
{'resource': 'ana@co', 'day': 0, 'shift': 'Morning'}
{'resource': 'ana@co', 'day': 1, 'shift': 'Morning'}
{'resource': 'ben@co', 'day': 0, 'shift': 'Night'}
```

`ana@co` is assigned her preferred shift and never `Night` on day 0, exactly
as configured.

---

## 6 — Break scheduling

Assign break start times to agent slots within each shift, ensuring that
simultaneous breaks never drop coverage below the required minimum:

```python
from pyworkforce.breaks import BreakScheduler

shifts_coverage     = {"Morning": [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
                       "Afternoon": [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1]}
scheduled_resources = {"Morning": [3], "Afternoon": [2]}
breaks = [{"name": "Lunch", "duration_periods": 2,
           "min_start_after": 2, "max_end_before": 2}]
min_coverage = [[2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1]]

scheduler = BreakScheduler(
    num_days=1, periods=16,
    shifts_coverage=shifts_coverage,
    scheduled_resources=scheduled_resources,
    breaks=breaks, min_coverage=min_coverage,
)
result = scheduler.solve()
print(result["status"])
for entry in result["break_schedule"]:
    print(entry)
```

```
OPTIMAL
{'shift': 'Morning',   'day': 0, 'slot': 0, 'break_name': 'Lunch', 'start_period': 2, 'end_period': 4}
{'shift': 'Morning',   'day': 0, 'slot': 1, 'break_name': 'Lunch', 'start_period': 4, 'end_period': 6}
{'shift': 'Morning',   'day': 0, 'slot': 2, 'break_name': 'Lunch', 'start_period': 2, 'end_period': 4}
{'shift': 'Afternoon', 'day': 0, 'slot': 0, 'break_name': 'Lunch', 'start_period': 10, 'end_period': 12}
{'shift': 'Afternoon', 'day': 0, 'slot': 1, 'break_name': 'Lunch', 'start_period': 12, 'end_period': 14}
```

---

## Documentation

The [documentation site](https://rodrigo-arenas.github.io/pyworkforce/stable/)
includes narrative guides, a full API reference, and self-contained tutorials
with real outputs:

- **[End-to-end tutorial](https://rodrigo-arenas.github.io/pyworkforce/stable/guide/end-to-end)**
  — demand forecast → queuing → staffing mix → shift coverage → schedule → roster
- **[Comparing scenarios](https://rodrigo-arenas.github.io/pyworkforce/stable/guide/scenarios)**
  — grids, DataFrames, and service-level sweeps
- **[API reference](https://rodrigo-arenas.github.io/pyworkforce/stable/api/queuing)**

Background reading on the underlying techniques:
[workforce planning](https://towardsdatascience.com/workforce-planning-optimization-using-python-69af0ef9011a)
and [scheduling](https://towardsdatascience.com/how-to-solve-scheduling-problems-in-python-36a9af8de451).

---

## Contributing

Contributions are very welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the
local development setup, how to run the tests and linter, and the pull-request
workflow.

## License

pyworkforce is released under the [MIT License](LICENSE).
