---
description: Explore PyWorkforce coverage and staffing curves with optional Matplotlib plotting functions that return composable Axes objects.
---

# API — Plotting

`pyworkforce.plotting` provides two functions for inspecting workforce results.
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
