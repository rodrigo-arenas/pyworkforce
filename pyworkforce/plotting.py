"""Optional Matplotlib charts for inspecting workforce plans and queue staffing."""

import numpy as np

from pyworkforce.utils.validation import check_positive_integer

__all__ = ["plot_coverage", "plot_period_shortfalls", "plot_staffing_curve"]


def _axes(ax):
    if ax is not None:
        return ax
    try:
        from matplotlib import pyplot as plt
    except ModuleNotFoundError as exc:
        if exc.name != "matplotlib":
            raise
        raise ImportError("Plotting requires Matplotlib. Install pyworkforce[plot].") from exc
    return plt.subplots(layout="constrained")[1]


def plot_coverage(coverage, *, day=0, ax=None):
    """Plot one day from a scheduler's ``coverage()`` DataFrame.

    Demand and scheduled staffing are drawn as steps. Shading marks shortfalls
    over the full period, including the final interval. Supply a Matplotlib
    Axes to compose charts. Returns the Axes and leaves display to the caller.
    """
    intervals = coverage.loc[coverage["day"] == day].sort_values("period")
    if intervals.empty:
        raise ValueError(f"coverage has no rows for day {day}")
    periods = intervals["period"].to_numpy()
    edges = np.append(periods, periods[-1] + 1)
    required = intervals["required"].to_numpy()
    scheduled = intervals["scheduled"].to_numpy()
    ax = _axes(ax)
    from matplotlib.ticker import MaxNLocator

    ax.stairs(required, edges, baseline=None, label="Required", color="#25304b", linestyle="--", linewidth=1.8)
    ax.stairs(scheduled, edges, baseline=None, label="Scheduled", color="#3451b2", linewidth=2.2)
    if (scheduled < required).any():
        shortfall_top = np.maximum(required, scheduled)
        ax.fill_between(
            edges, np.append(scheduled, scheduled[-1]), np.append(shortfall_top, shortfall_top[-1]),
            step="post", color="#d0673d", alpha=0.25, label="Shortfall",
        )
    ax.set(title=f"Coverage · day {day}", xlabel="Period boundary", ylabel="People", xlim=(edges[0], edges[-1]))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    return ax


def plot_period_shortfalls(shortfalls, *, limit=8, ax=None):
    """Show the leading rows of a scheduler's ``compare_coverage(..., by_period=True)``.

    Values are people short in each interval. The row and scenario order of the
    input table is preserved. A dash marks a missing cell in a reindexed table.
    Returns the Matplotlib Axes.
    """
    check_positive_integer("limit", limit)
    if shortfalls.empty or list(shortfalls.index.names) != ["day", "period"]:
        raise ValueError("shortfalls must be a non-empty table indexed by (day, period)")
    shown = shortfalls.head(limit)
    values = shown.to_numpy(dtype=float, na_value=np.nan)
    observed = values[~np.isnan(values)]
    if not np.isfinite(observed).all() or (observed < 0).any() or (observed != np.floor(observed)).any():
        raise ValueError("shortfalls must be non-negative whole headcounts or missing")

    ax = _axes(ax)
    from matplotlib import colormaps

    peak = max(1, observed.max()) if observed.size else 1
    ax.imshow(values, aspect="auto", interpolation="nearest", vmin=0, vmax=peak,
              cmap=colormaps["Blues"].with_extremes(bad="#e2e2e2"))
    for row, counts in enumerate(shown.itertuples(index=False, name=None)):
        for column, count in enumerate(counts):
            value = values[row, column]
            label = "—" if np.isnan(value) else str(int(count))
            color = "white" if value > 0.6 * peak else "#172738"
            ax.text(column, row, label, ha="center", va="center", color=color)

    ax.set_xticks(range(len(shown.columns)), labels=[str(name) for name in shown.columns])
    ax.set_yticks(range(len(shown)), labels=[f"{day} / {period}" for day, period in shown.index])
    ax.set(title="Staffing shortfall (people)", ylabel="Day / period")
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0)
    if np.isnan(values).any():
        ax.set_xlabel("—  Missing observation")
    return ax


def plot_staffing_curve(curve, *, ax=None):
    """Plot achieved service level and occupancy from ``ErlangC.staffing_curve()``.

    Headcounts are drawn in ascending order. Supply a Matplotlib Axes to compose
    charts. Returns the Axes and leaves display to the caller.
    """
    if curve.empty:
        raise ValueError("staffing curve must contain at least one candidate")
    ordered = curve.sort_values("positions")
    ax = _axes(ax)
    from matplotlib.ticker import MaxNLocator, PercentFormatter

    ax.plot(ordered["positions"], ordered["service_level"], label="Service level", color="#3451b2", marker="o")
    ax.plot(ordered["positions"], ordered["occupancy"], label="Occupancy", color="#a24d32", marker="s", linestyle="--")
    ax.set(title="Erlang C staffing trade-off", xlabel="Positions", ylabel="Rate", ylim=(0, 1.05))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    return ax
