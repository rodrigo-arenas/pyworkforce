"""Optional Matplotlib charts for inspecting workforce plans and queue staffing."""

import numpy as np

__all__ = ["plot_coverage", "plot_staffing_curve"]


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
