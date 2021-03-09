# pyworkforce
Common tools for workforce management, schedule and optimization problems.


### Queue systems:

It can be used for solving the required number of positions to manage a number of transactions,
under some systems pre-defined parameters and goals.


#### Example:

```python
from pyworkforce.queuing.erlang import ErlangC

erlang = ErlangC(transactions=100, asa=20/60, aht=3, interval=30, shrinkage=0.3)

positions_requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print("positions_requirements: ", positions_requirements)


>> positions_requirements:  {'raw_positions': 14, 
                             'positions': 20, 
                             'service_level': 0.8883500191794669, 
                             'occupancy': 0.7142857142857143, 
                             'waiting_probability': 0.1741319335950498}
```
