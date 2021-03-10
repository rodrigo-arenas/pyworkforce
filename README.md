# pyworkforce
Common tools for workforce management, schedule and optimization problems built in top of tools like google's ortools 
and custom modules

# Usage:
For complete list and details of examples go to the 
[examples folder](https://github.com/rodrigo-arenas/pyworkforce/tree/develop/examples)

### Queue systems:

It can be used for solving the required number of positions to manage a number of transactions,
under some systems pre-defined parameters and goals.


#### Example:

```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, asa=20/60, aht=3, interval=30, shrinkage=0.3)

positions_requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print("positions_requirements: ", positions_requirements)


>> positions_requirements:  {'raw_positions': 14, 
                             'positions': 20, 
                             'service_level': 0.8883500191794669, 
                             'occupancy': 0.7142857142857143, 
                             'waiting_probability': 0.1741319335950498}
```

### Shifts Design

Find the optimal number of persons to assign to a pre-defined list of shifts, under a requirement of persons per period 
of day and capacity restrictions

#### Example:

```python
from pyworkforce.shifts import MinAbsDifference

# Rows are the days, each entry of a row, is an hour of the day (24). 
required_resources = [
    [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
    [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
]

# Each entry of a shift, is an hour of the day (24)
shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                   "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                   "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}


scheduler = MinAbsDifference(num_days=2,
                             periods=24,
                             shifts_coverage=shifts_coverage,
                             required_resources=required_resources,
                             max_period_concurrency=25,
                             max_shift_concurrency=20)

solution = scheduler.solve()
print("solution :", solution)

>> solution: {'status': 'OPTIMAL', 
              'cost': 157.0, 
              'resources_shifts': [{'day': 0, 'shift': 'Morning', 'resources': 8},
                                   {'day': 0, 'shift': 'Afternoon', 'resources': 11},
                                   {'day': 0, 'shift': 'Night', 'resources': 9}, 
                                   {'day': 0, 'shift': 'Mixed', 'resources': 1}, 
                                   {'day': 1, 'shift': 'Morning', 'resources': 13}, 
                                   {'day': 1, 'shift': 'Afternoon', 'resources': 17}, 
                                   {'day': 1, 'shift': 'Night', 'resources': 13}, 
                                   {'day': 1, 'shift': 'Mixed', 'resources': 0}]
              }
```