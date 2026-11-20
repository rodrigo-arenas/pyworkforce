---
description: Explore PyWorkforce coverage and staffing curves with optional Matplotlib plotting functions that return composable Axes objects.
---

# API — Plotting

`pyworkforce.plotting` provides functions for inspecting workforce results.
Install `pyworkforce[plot]` to create charts. Each function returns the
Matplotlib `Axes` it drew on. Pass `ax` to compose a figure, or omit it to
create a new figure. Call `ax.figure.savefig(...)` or `matplotlib.pyplot.show()`
when ready to export or display your result.

## `plot_coverage(coverage, *, day=0, ax=None)`

Pass the DataFrame returned by a shift scheduler's `coverage()` method.
`day` selects a zero-based planning day. The horizontal axis marks the boundaries
of each period, with scheduled and required headcounts drawn as steps. Shading
marks intervals with a shortfall. A day absent from the frame raises `ValueError`.

See the [schedule stress-test tutorial](/guide/coverage-scenarios).

## `plot_staffing_curve(curve, *, ax=None)`

Pass the DataFrame returned by `ErlangC.staffing_curve()`. The chart orders
candidates by headcount and displays service level and occupancy as percentages.
The headcount axis uses the counts supplied to `staffing_curve()`. It represents
scheduled or productive positions according to that call's `scale_positions`.

See the [staffing curve tutorial](/guide/staffing-curve).

## `plot_period_shortfalls(shortfalls, *, limit=8, ax=None)`

Pass the table from `compare_coverage(scenarios, by_period=True)`. The chart
shows its first `limit` rows in table order, including covered intervals when
they fall within the limit. Each cell gives the number of additional people
needed in that interval. Bars share a common scale across the displayed cells.
The longest bar fills its track. A framed cell and a bold interval label mark
each maximum positive shortfall, including ties. A zero means fully covered. A dash marks a missing
value if you reindex the table. Use a positive integer for `limit` and select
the columns of interest when comparing many scenarios.

See the [ranked shortfalls example](/guide/coverage-scenarios#which-interval-needs-extra-people-first).
