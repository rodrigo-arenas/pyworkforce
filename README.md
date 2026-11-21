[![Tests](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml/badge.svg?branch=main)](https://github.com/rodrigo-arenas/pyworkforce/actions/workflows/ci-tests.yml)
[![Codecov](https://codecov.io/gh/rodrigo-arenas/pyworkforce/branch/main/graphs/badge.svg?branch=main&service=github)](https://codecov.io/github/rodrigo-arenas/pyworkforce?branch=main)
[![PyPI Version](https://badge.fury.io/py/pyworkforce.svg)](https://pypi.org/project/pyworkforce/)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-pyworkforce.rodrigo--arenas.com-blue)](https://pyworkforce.rodrigo-arenas.com/stable/)

# pyworkforce

**Practical workforce planning in Python: queue staffing, shift scheduling, rostering, and breaks.**

pyworkforce helps teams turn variable demand into staffing decisions with a friendly,
scikit-learn-like API. It combines Erlang queueing models and OR-Tools
constraint programming so workforce analysts, data scientists, operations
researchers, and Python developers can move from forecast volumes to workable
staffing plans without building every solver from scratch.

It is useful for contact centers and call centers, but the same patterns apply
to healthcare staffing, retail operations, logistics, support teams, service
desks, and field operations.

**Docs:** [pyworkforce.rodrigo-arenas.com](https://pyworkforce.rodrigo-arenas.com/stable/)  
**Package:** [PyPI](https://pypi.org/project/pyworkforce/)  
**Examples:** [examples/](examples/)

## Why pyworkforce?

- **More practical than spreadsheets:** reusable models, scenario sweeps, tested
  calculations, and outputs that fit naturally into pandas workflows.
- **Faster than custom scripts:** common workforce planning steps are packaged
  behind consistent constructors, `solve()` methods, validation, and clear
  result dictionaries.
- **Lighter than enterprise WFM tools:** use it inside notebooks, pipelines,
  internal apps, simulations, or decision-support workflows without adopting a
  full platform.
- **Built on proven methods:** Erlang C, Erlang A, and Erlang B for queue
  staffing; OR-Tools CP-SAT for scheduling, rostering, and break placement.
- **Designed for adoption:** small examples, copy-paste tutorials, and APIs that
  feel familiar to Python users.

## Installation

```bash
pip install pyworkforce
```

pyworkforce supports Python 3.12, 3.13, and 3.14.

Install the plotting extra to explore coverage and Erlang C staffing curves
with Matplotlib:

```bash
pip install "pyworkforce[plot]"
```

The [schedule stress-test tutorial](https://pyworkforce.rodrigo-arenas.com/stable/guide/coverage-scenarios)
shows how to set staffing limits by shift and compare a solved plan against
multiple demand forecasts. The [Erlang C staffing curve tutorial](https://pyworkforce.rodrigo-arenas.com/stable/guide/staffing-curve)
shows how to choose a headcount against service and occupancy targets.

## Planning pipeline

![Queue sizing can supply agent requirements to shift scheduling or per-skill targets to skill-mix optimization. A solved shift schedule supplies daily headcounts to both rostering and break scheduling.](https://raw.githubusercontent.com/rodrigo-arenas/pyworkforce/main/docs/images/planning_pipeline.svg)

This overview follows the `main` branch. For published versions, see the
[release notes](https://pyworkforce.rodrigo-arenas.com/stable/release-notes).

Start with your own staffing requirements or derive agent counts from queue traffic.
Use `pyworkforce.shifts` to build shift coverage from hours, spans, or period indices.
After solving a shift schedule, `scheduled_resources()` gives counts by shift and day.
Pass them as `required_resources` to the roster or as `scheduled_resources` to the
break scheduler, along with each tool's constraints.

| Planning decision | API | Result |
| --- | --- | --- |
| Size a queue | `ErlangA`, `ErlangC`, `ErlangB` and batch variants `MultiErlangA`, `MultiErlangC`, `MultiErlangB` | Agents for service targets (A/C), or channels for a blocking target (B) |
| Choose a skill mix | `MultiSkillStaffing` | Minimum-cost headcount by skill profile |
| Cover period demand with shifts | `MinRequiredResources`, `MinAbsDifference` | People per shift and day |
| Check a solved plan | `coverage()`, `compare_coverage(..., by_period=True)` | Coverage per interval and a ranked table of scenario shortfalls |
| Assign named people | `MinHoursRoster` | Assignments and days off, with optional shift consistency by block |
| Place breaks | `BreakScheduler` | Break start periods for anonymous slots while maintaining minimum coverage |

Optional Matplotlib views include `plot_staffing_curve()` for Erlang C,
`plot_coverage()` for a single day, and `plot_period_shortfalls()` for comparing scenarios.

## What can I do in 5 minutes?

### Size a contact-center queue with Erlang C

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(
    transactions=100,  # calls in the interval
    aht=3,             # average handle time, minutes
    asa=20 / 60,       # answer-time target, minutes
    interval=30,       # interval length, minutes
    shrinkage=0.30,
)

print(erlang.required_positions(service_level=0.80, max_occupancy=0.85))
```

```text
{'raw_positions': 14,
 'positions': 20,
 'service_level': 0.8883500191794669,
 'occupancy': 0.7142857142857143,
 'waiting_probability': 0.1741319335950498}
```

`raw_positions` is productive staffing. `positions` adds shrinkage for breaks,
training, meetings, and other unavailable time.

### Compare staffing scenarios

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

param_grid = {
    "transactions": [80, 100, 120],
    "aht": [3],
    "asa": [20 / 60],
    "interval": [30],
    "shrinkage": [0.20, 0.30],
}

multi = MultiErlangC(param_grid=param_grid, n_jobs=-1)
results = multi.required_positions({"service_level": [0.80], "max_occupancy": [0.85]})
df = results_to_dataframe(results, multi.required_positions_params)
print(df[["transactions", "shrinkage", "positions", "service_level"]])
```

Use this pattern to compare service levels, shrinkage assumptions, average
handle time, patience, or arrival forecasts.

### Build shift coverage from clock hours

```python
from pyworkforce.shifts import shift_coverage_from_hours

shifts_coverage = shift_coverage_from_hours(
    {
        "Morning": (6, 14),
        "Afternoon": (14, 22),
        "Night": (22, 6),  # wraps past midnight
    },
    num_periods=24,
)
```

The result feeds the scheduling solvers directly, avoiding hand-written 0/1
coverage arrays.

## Main capabilities

| Capability | Use it when | Start here |
| --- | --- | --- |
| Erlang C staffing | Callers wait and abandonment is ignored or negligible | [Erlang C guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/erlangc) |
| Erlang A staffing | Callers may abandon before being answered | [Erlang A guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/erlanga) |
| Erlang B channel sizing | Blocked calls are lost because there is no queue | [Erlang B guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/erlangb) |
| Multi-skill staffing | Agents can cover different skill combinations | [Staffing guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/staffing) |
| Shift scheduling | You need shift counts from hourly demand | [Scheduling guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/scheduling) |
| Employee rostering | You need named assignments with rules and preferences | [Rostering guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/rostering) |
| Break scheduling | You need meal/rest breaks while maintaining coverage | [Break guide](https://pyworkforce.rodrigo-arenas.com/stable/guide/breaks) |

## Project status

pyworkforce is beta-stage open source software. The core models are tested and
usable for real planning experiments, but workforce policies vary by operation,
country, and labor agreement. Validate assumptions, units, and constraints
against your own environment before using results operationally.

## Documentation

- [Get Started](https://pyworkforce.rodrigo-arenas.com/stable/guide/introduction)
- [Quick Start](https://pyworkforce.rodrigo-arenas.com/stable/guide/quickstart)
- [End-to-end planning tutorial](https://pyworkforce.rodrigo-arenas.com/stable/guide/end-to-end)
- [Recipes](https://pyworkforce.rodrigo-arenas.com/stable/recipes/)
- [API Reference](https://pyworkforce.rodrigo-arenas.com/stable/api/queuing)
- [Release Notes](https://pyworkforce.rodrigo-arenas.com/stable/release-notes)

## Contributing

Contributions are welcome: examples, documentation, validation improvements,
benchmarks, visualization helpers, additional workforce constraints, and bug
reports all help. See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup,
tests, docs, and roadmap ideas.

## License

pyworkforce is released under the [MIT License](LICENSE).
