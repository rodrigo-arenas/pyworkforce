"""Optional Matplotlib charts for inspecting workforce plans and queue staffing."""

from textwrap import fill

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
    Bars share a zero baseline and scale to the largest displayed shortfall.
    Peak cells are framed, including ties. Returns the Matplotlib Axes.
    """
    check_positive_integer("limit", limit)
    if shortfalls.empty or list(shortfalls.index.names) != ["day", "period"]:
        raise ValueError("shortfalls must be a non-empty table indexed by (day, period)")
    shown = shortfalls.head(limit)
    values = shown.to_numpy(dtype=float, na_value=np.nan)
    observed = values[~np.isnan(values)]
    if not np.isfinite(observed).all() or (observed < 0).any() or (observed != np.floor(observed)).any():
        raise ValueError("shortfalls must be non-negative whole headcounts or missing")

    supplied_axes = ax is not None
    ax = _axes(ax)
    from matplotlib.patches import FancyBboxPatch

    rows, columns = shown.shape
    if not supplied_axes:
        ax.figure.set_size_inches(max(5.2, 1.2 + 1.35 * columns), max(2.4, 1.0 + 0.56 * rows))
    ax.set(xlim=(-0.5, columns - 0.5), ylim=(rows - 0.5, -0.5))
    ax.grid(False)
    ax.spines[:].set_visible(False)

    # Determine ties using the original integers, including counts above 2**53.
    original = shown.to_numpy(dtype=object)
    peak = max(map(int, original[~np.isnan(values)]), default=0)
    ink = "#163d43"
    muted = "#526773"
    column_inches = ax.get_window_extent().width / ax.figure.dpi / columns
    peak_rows = set()
    for row, counts in enumerate(original):
        if row % 2 == 0:
            ax.axhspan(row - 0.5, row + 0.5, color="#f3f6f5", linewidth=0)
        for column, count in enumerate(counts):
            missing = np.isnan(values[row, column])
            amount = 0 if missing else int(count)
            is_peak = amount > 0 and amount == peak
            if is_peak:
                peak_rows.add(row)
                ax.add_patch(FancyBboxPatch(
                    (column - 0.45, row - 0.43), 0.9, 0.86,
                    boxstyle="round,pad=0,rounding_size=0.065", linewidth=1.2,
                    edgecolor=ink, facecolor=ink,
                ))
            label = "—" if missing else str(amount)
            label_size = min(13 if amount else 10, 95 * column_inches / len(label))
            ax.text(column, row - 0.09 if amount else row, label, ha="center", va="center",
                    fontsize=label_size, fontweight="bold" if amount else "normal",
                    color="white" if is_peak else ink if amount else muted)
            if amount:
                # Every track starts at zero and spans the largest displayed shortfall.
                left = column - 0.31
                ax.hlines(row + 0.21, left, left + 0.62, colors="#90b0b2" if is_peak else "#d9e4e2", linewidth=3)
                ax.hlines(row + 0.21, left, left + 0.62 * amount / peak,
                          colors="#f3bf72" if is_peak else "#34797b", linewidth=3)

    ax.hlines(np.arange(rows + 1) - 0.5, -0.5, columns - 0.5, colors="#cfdbd8", linewidth=0.65)
    ax.vlines(np.arange(1, columns) - 0.5, -0.5, rows - 0.5, colors="#e0e7e5", linewidth=0.6)
    # Wrap to the supplied subplot width without changing the caller's figure.
    wrap_at = max(4, int((column_inches - 0.06) * 15))
    headings = []
    for name in shown.columns:
        lines = fill(str(name), width=wrap_at, break_long_words=False).splitlines()
        headings.append("\n".join(fill(line, width=wrap_at) for line in lines))
    ax.set_xticks(range(columns), labels=headings, fontsize=9, fontweight="bold", color=ink)
    ax.set_yticks(range(rows), labels=[f"{day} / {period}" for day, period in shown.index],
                  fontsize=10, color=ink)
    for row in peak_rows:
        ax.get_yticklabels()[row].set_fontweight("bold")
    title = ax.set_title("Staffing shortfall (people)", fontsize=15, fontweight="bold", color=ink, pad=14)
    title.set(x=0, ha="left")
    ax.set_ylabel("Day / period", fontsize=9, color=muted)
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0, pad=7)
    if np.isnan(values).any():
        ax.set_xlabel("—  Missing observation", fontsize=9, color=muted)
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
