# API — Shifts

`pyworkforce.shifts`

Helpers to build and inspect `shifts_coverage` dictionaries. See the
[shift coverage guide](/guide/shifts).

## shift_coverage_from_hours

```python
shift_coverage_from_hours(hours_by_shift, num_periods=24,
                          period_minutes=60, wrap_around=True)
```

Build coverage from `{shift_name: (start_hour, end_hour)}` on a 24-hour clock.
Overnight windows (`end_hour <= start_hour`) wrap past midnight when
`wrap_around=True`. `num_periods * period_minutes` must equal `1440`. Windows
must align with the period grid; a full-day shift is `(0, 24)`.

Returns `{shift_name: [0/1, …]}`.

## shift_coverage_from_spans

```python
shift_coverage_from_spans(spans_by_shift, num_periods, wrap_around=True)
```

Build coverage from `(start_period, length)` spans, or a list of such spans for
split shifts. Spans extending past the day wrap when `wrap_around=True`.

Returns `{shift_name: [0/1, …]}`.

## shift_coverage_from_periods

```python
shift_coverage_from_periods(periods_by_shift, num_periods)
```

Build coverage from explicit zero-based period indices
`{shift_name: [indices…]}`.

Returns `{shift_name: [0/1, …]}`.

## validate_shift_coverage

```python
validate_shift_coverage(shifts_coverage, num_periods=None)
```

Validate that the dictionary is non-empty, all arrays share the same length and
all values are `0`/`1`. Returns the number of periods. Raises `ValueError`
otherwise.

## coverage_to_dataframe

```python
coverage_to_dataframe(shifts_coverage)
```

Return a `pandas.DataFrame` view (rows = shifts, columns = period indices).
