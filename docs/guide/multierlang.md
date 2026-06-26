# Running many scenarios with MultiErlang*

The `MultiErlang*` classes — `MultiErlangC`, `MultiErlangA` and `MultiErlangB`
— evaluate their respective Erlang model over **many parameter combinations at
once**.
Its interface is inspired by scikit-learn's grid-search utilities: you provide
a `param_grid` of constructor arguments, then call a method with an
`arguments_grid`. Every combination of the two grids is evaluated, in parallel
via [joblib](https://joblib.readthedocs.io/).

## Example

```python
from pyworkforce.queuing import MultiErlangC

param_grid = {
    "transactions": [100],
    "aht": [3],
    "interval": [30],
    "asa": [20 / 60],
    "shrinkage": [0.3],
}
multi = MultiErlangC(param_grid=param_grid, n_jobs=-1)

scenarios = {"service_level": [0.8, 0.85, 0.9], "max_occupancy": [0.8]}
results = multi.required_positions(scenarios)
```

`results` is a list with one dictionary per combination, in deterministic
order:

```text
[{'raw_positions': 13, 'positions': 19, 'service_level': 0.795..., ...},
 {'raw_positions': 14, 'positions': 20, 'service_level': 0.888..., ...},
 {'raw_positions': 15, 'positions': 22, 'service_level': 0.941..., ...}]
```

## Which parameters produced each result?

After calling a method, the matching parameter combinations are stored on the
estimator in the **same order** as the results:

```python
multi.required_positions_params      # for required_positions
multi.service_level_params           # for service_level
multi.waiting_probability_params     # for waiting_probability
multi.achieved_occupancy_params      # for achieved_occupancy
```

Each entry is a `(erlang_params, method_params)` tuple, which makes it easy to
zip results back to their inputs:

```python
for (erlang_params, method_params), result in zip(
        multi.required_positions_params, results):
    print(erlang_params["transactions"], method_params["service_level"],
          "->", result["positions"])
```

## Available methods

`MultiErlangC` mirrors `ErlangC`:

- `required_positions(arguments_grid)`
- `service_level(arguments_grid)`
- `waiting_probability(arguments_grid)`
- `achieved_occupancy(arguments_grid)`

`MultiErlangA` adds abandonment-specific methods:

- all of the above, plus `abandonment_probability`, `average_speed_of_answer`,
  `average_queue_length`. `param_grid` takes `ErlangA` constructor arguments
  (including `patience`).

`MultiErlangB` mirrors `ErlangB` (loss queue):

- `required_positions(arguments_grid)` — `arguments_grid` takes `max_blocking`
  and optionally `max_occupancy`.
- `blocking_probability(arguments_grid)` — `arguments_grid` takes `positions`.
- `achieved_occupancy(arguments_grid)` — `arguments_grid` takes `positions`.

## Parallelism

`n_jobs` controls the number of parallel workers (`-1` uses all CPUs, `1`
disables parallelism — handy for debugging). `pre_dispatch` follows joblib's
semantics. See the [joblib docs](https://joblib.readthedocs.io/) for details.
