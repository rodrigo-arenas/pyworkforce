# API — Queuing

`pyworkforce.queuing`

## ErlangC

```python
ErlangC(transactions, aht, asa, interval, shrinkage=0.0)
```

Erlang C (M/M/c) queue: Poisson arrivals, exponential handling times, infinite
queue, no abandonment.

**Parameters**

- **transactions** (`float`) — transactions arriving in the interval.
- **aht** (`float`) — average handle time.
- **asa** (`float`) — target average speed of answer.
- **interval** (`float`) — interval length.
- **shrinkage** (`float`, default `0.0`) — unavailable fraction, in `[0, 1)`.

**Attributes**

- **intensity** (`float`) — offered load in Erlangs.

**Methods**

- `required_positions(service_level, max_occupancy=1.0)` → `dict` with
  `raw_positions`, `positions`, `service_level`, `occupancy`,
  `waiting_probability`.
- `waiting_probability(positions, scale_positions=False)` → `float`
- `service_level(positions, scale_positions=False)` → `float`
- `achieved_occupancy(positions, scale_positions=False)` → `float`
- `get_params()` → `dict`

Set `scale_positions=True` when `positions` already includes shrinkage.

See the [Erlang C guide](/guide/erlangc).

## ErlangA

```python
ErlangA(transactions, aht, asa, interval, patience, shrinkage=0.0)
```

Erlang A (M/M/c+M) queue with customer abandonment. All metrics are computed
exactly from the birth-death stationary distribution.

**Parameters** — as `ErlangC`, plus:

- **patience** (`float`) — mean time before a waiting customer abandons.

**Methods**

- `required_positions(service_level, max_occupancy=1.0, max_abandonment=1.0, asa=None)`
  → `dict` with `raw_positions`, `positions`, `service_level`, `occupancy`,
  `abandonment_probability`, `waiting_probability`, `average_speed_of_answer`.
- `waiting_probability(positions)` → `float`
- `abandonment_probability(positions)` → `float`
- `achieved_occupancy(positions)` → `float`
- `average_speed_of_answer(positions)` → `float`
- `average_queue_length(positions)` → `float`
- `service_level(positions, asa=None)` → `float`
- `get_params()` → `dict`

See the [Erlang A guide](/guide/erlanga).

## MultiErlangC

```python
MultiErlangC(param_grid, n_jobs=2, pre_dispatch='2 * n_jobs')
```

Evaluate `ErlangC` over a grid of parameters in parallel.

**Parameters**

- **param_grid** (`dict`) — `ErlangC` constructor arguments, each mapped to a
  list of values.
- **n_jobs** (`int`, default `2`) — parallel workers (`-1` = all CPUs).
- **pre_dispatch** (`str`, default `'2 * n_jobs'`) — joblib pre-dispatch.

**Methods** (each takes an `arguments_grid` dict and returns a list of results)

- `required_positions(arguments_grid)`
- `service_level(arguments_grid)`
- `waiting_probability(arguments_grid)`
- `achieved_occupancy(arguments_grid)`

**Attributes** (set after the matching method runs, aligned with results)

- `required_positions_params`, `service_level_params`,
  `waiting_probability_params`, `achieved_occupancy_params` — lists of
  `(erlang_params, method_params)` tuples.

See the [MultiErlangC guide](/guide/multierlang).
