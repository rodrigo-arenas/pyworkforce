# Tutorial: comparing scenarios with grids and DataFrames

Planning rarely uses a single set of assumptions. The `Multi*` estimators
evaluate **many scenarios at once**, and `results_to_dataframe` turns the
results into a tidy table you can sort, filter and plot. Every output below is
the real output of the snippet.

## Sweeping Erlang C service-level targets

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

param_grid = {
    "transactions": [100], "aht": [3], "interval": [30],
    "asa": [20 / 60], "shrinkage": [0.3],
}
multi = MultiErlangC(param_grid=param_grid, n_jobs=1)

results = multi.required_positions({"service_level": [0.8, 0.9], "max_occupancy": [0.85]})
df = results_to_dataframe(results, multi.required_positions_params)

print(df[["service_level", "service_level_result", "positions", "occupancy"]].round(4).to_string(index=False))
```

```text
 service_level  service_level_result  positions  occupancy
           0.8                0.8884         20     0.7143
           0.9                0.9415         22     0.6667
```

Note the two `service_level` columns: the input **target** stays under
`service_level`, while the **achieved** value is preserved as
`service_level_result` (pyworkforce suffixes result keys that would otherwise
collide with an input name).

## How patience changes Erlang A staffing

Here we sweep the `patience` parameter to see how customer impatience affects
required staffing, using [`MultiErlangA`](/guide/erlanga).

```python
from pyworkforce.queuing import MultiErlangA
from pyworkforce.utils import results_to_dataframe

grid = {
    "transactions": [100], "aht": [3], "interval": [30],
    "asa": [20 / 60], "patience": [3, 5, 10], "shrinkage": [0.3],
}
multi = MultiErlangA(param_grid=grid, n_jobs=1)

results = multi.required_positions(
    {"service_level": [0.8], "max_occupancy": [0.85], "max_abandonment": [0.05]}
)
df = results_to_dataframe(results, multi.required_positions_params)

cols = ["patience", "raw_positions", "positions", "service_level_result", "abandonment_probability"]
print(df[cols].round(4).to_string(index=False))
```

```text
 patience  raw_positions  positions  service_level_result  abandonment_probability
        3             13         19                0.8751                   0.0322
        5             13         19                0.8582                   0.0250
       10             13         19                0.8376                   0.0165
```

As customers become more patient, fewer abandon, so the achieved service level
drops slightly for the same staffing while the abandonment probability falls —
useful when deciding how conservative your staffing should be.

## Scalar metrics across positions

The `Multi*` methods that return a single number (like `service_level`) also
work with the grid. Each result lines up with the matching `*_params` entry.

```python
from pyworkforce.queuing import MultiErlangC
from pyworkforce.utils import results_to_dataframe

multi = MultiErlangC(
    param_grid={"transactions": [100], "aht": [3], "interval": [30],
                "asa": [20 / 60], "shrinkage": [0.0]},
    n_jobs=1,
)
sl = multi.service_level({"positions": [11, 12, 13, 14]})
df = results_to_dataframe(sl, multi.service_level_params)
print(df[["positions", "result"]].round(4).to_string(index=False))
```

```text
 positions  result
        11  0.3896
        12  0.6402
        13  0.7956
        14  0.8884
```

Scalar results are placed in a `result` column. From a DataFrame it is a short
hop to plotting a staffing curve or exporting a planning table to CSV.
