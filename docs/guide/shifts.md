# Building shift coverage

The scheduling solvers expect a `shifts_coverage` dictionary that maps each
shift name to a **0/1 array of length `periods`**, where `1` means the shift
covers that period. Writing those arrays by hand is tedious and error prone, so
`pyworkforce.shifts` provides small, deterministic builders.

```python
from pyworkforce.shifts import (
    shift_coverage_from_hours,
    shift_coverage_from_spans,
    shift_coverage_from_periods,
    validate_shift_coverage,
    coverage_to_dataframe,
)
```

## From clock hours

The most natural option: describe each shift by its `(start_hour, end_hour)` on
a 24-hour clock. Overnight shifts (where `end <= start`) wrap past midnight.

```python
shifts_coverage = shift_coverage_from_hours({
    "Morning":   (6, 14),
    "Afternoon": (14, 22),
    "Night":     (22, 6),   # wraps past midnight
}, num_periods=24)
```

For finer granularity, set `period_minutes`. For example, 30-minute periods
give 48 periods per day:

```python
shift_coverage_from_hours({"Early": (8, 8.5)},
                          num_periods=48, period_minutes=30)
```

The window must align with the period grid (`num_periods * period_minutes`
must equal a full day, 1440 minutes), and a full-day shift is written `(0, 24)`.

## From spans

Describe a shift by a `(start_period, length)` span, optionally as a list of
blocks. Spans that run off the end of the day wrap around when
`wrap_around=True` (the default):

```python
shift_coverage_from_spans({"Night": (21, 8)}, num_periods=24)
shift_coverage_from_spans({"Split": [(8, 2), (14, 2)]}, num_periods=24)
```

## From explicit period indices

When you want full control, list exactly which periods each shift covers:

```python
shift_coverage_from_periods({"Morning": [6, 7, 8, 9, 10]}, num_periods=24)
```

## Validate and visualize

`validate_shift_coverage` checks that every array has the same length and only
contains 0/1 values, returning the number of periods:

```python
validate_shift_coverage(shifts_coverage)   # -> 24
```

`coverage_to_dataframe` returns a `pandas.DataFrame` (rows = shifts, columns =
periods), which is handy for inspecting coverage in a notebook:

```python
coverage_to_dataframe(shifts_coverage)
```

## Feeding the schedulers

The output plugs straight into the [scheduling](/guide/scheduling) solvers:

```python
from pyworkforce.scheduling import MinRequiredResources

scheduler = MinRequiredResources(
    num_days=2, periods=24,
    shifts_coverage=shifts_coverage,
    required_resources=required_resources,
    max_period_concurrency=30, max_shift_concurrency=30,
)
```
