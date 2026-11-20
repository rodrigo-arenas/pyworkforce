import sys

import matplotlib
import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from pyworkforce.plotting import plot_coverage, plot_period_shortfalls, plot_staffing_curve
from pyworkforce.queuing import ErlangC
from pyworkforce.scheduling import MinAbsDifference

matplotlib.use('Agg')


def test_plot_coverage_shows_demand_and_scheduled_headcount_for_requested_day():
    scheduler = MinAbsDifference(2, 2, {'all day': [1, 1]}, [[1, 1], [2, 5]], 2, 2, num_search_workers=1)
    scheduler.solve()
    ax = plot_coverage(scheduler.coverage(), day=1)
    try:
        demand, scheduled = ax.patches
        assert demand.get_data().values.tolist() == [2, 5]
        assert scheduled.get_data().values.tolist() == [2, 2]
        assert demand.get_data().edges.tolist() == [0, 1, 2]
        region = ax.collections[0].get_paths()[0].vertices
        assert region[:, 0].max() == 2
        assert region[:, 1].max() == 5
    finally:
        plt.close(ax.figure)
    with pytest.raises(ValueError, match='day'):
        plot_coverage(scheduler.coverage(), day=2)


def test_plot_staffing_curve_reuses_custom_axes_and_orders_by_positions():
    curve = ErlangC(100, 3, 20 / 60, 30).staffing_curve([15, 13, 14])
    figure, original_ax = plt.subplots()
    try:
        ax = plot_staffing_curve(curve, ax=original_ax)
        assert ax is original_ax
        service, occupancy = ax.lines
        assert list(service.get_xdata()) == [13, 14, 15]
        assert list(service.get_ydata()) == pytest.approx(curve.sort_values('positions')['service_level'].to_numpy())
        assert list(occupancy.get_ydata()) == pytest.approx([10 / 13, 10 / 14, 10 / 15])
    finally:
        plt.close(figure)


def test_plotting_names_the_optional_extra_when_matplotlib_is_unavailable(monkeypatch):
    curve = ErlangC(100, 3, 20 / 60, 30).staffing_curve([14])
    monkeypatch.setitem(sys.modules, 'matplotlib', None)
    monkeypatch.delitem(sys.modules, 'pyworkforce.plotting')
    from pyworkforce.plotting import plot_staffing_curve as plot_without_matplotlib

    with pytest.raises(ImportError, match=r'pyworkforce\[plot\]'):
        plot_without_matplotlib(curve)


def test_plot_period_shortfalls_labels_and_limits_on_supplied_axes():
    scheduler = MinAbsDifference(1, 2, {"day": [1, 1]}, [[1, 1]], 1, 1)
    scheduler.solve()
    table = scheduler.compare_coverage({"Rush": [[1, 4]], "Base": None}, by_period=True)
    # Align with an unobserved forecast as an analyst might do in a notebook.
    table = table.reindex(columns=["Rush", "Base", "Unobserved"])
    figure, ax = plt.subplots()
    try:
        assert plot_period_shortfalls(table, limit=1, ax=ax) is ax
        assert ax.get_title() == "Staffing shortfall (people)"
        assert ax.get_ylabel() == "Day / period"
        assert "Missing" in ax.get_xlabel()
        assert [t.get_text() for t in ax.get_xticklabels()] == ["Rush", "Base", "Unobserved"]
        assert [t.get_text() for t in ax.get_yticklabels()] == ["0 / 1"]
        assert [t.get_text() for t in ax.texts] == ["3", "0", "—"]
        assert [t.get_fontweight() for t in ax.texts] == ["bold", "normal", "normal"]
        assert ax.get_yticklabels()[0].get_fontweight() == "bold"
        assert ax.get_xlim() == (-0.5, 2.5)
        ax.set_title("Alternative forecast")
        assert ax.get_title() == "Alternative forecast"
    finally:
        plt.close(figure)


@pytest.mark.parametrize(("count", "label"), [(0, "0"), (pd.NA, "—"), (2**53 + 1, str(2**53 + 1))])
def test_plot_period_shortfalls_single_interval_and_exact_annotation(count, label):
    index = pd.MultiIndex.from_tuples([(0, 0)], names=["day", "period"])
    table = pd.DataFrame({"Base": pd.array([count], dtype="Int64")}, index=index)
    ax = plot_period_shortfalls(table)
    try:
        assert [text.get_text() for text in ax.texts] == [label]
        assert ax.get_yticklabels()[0].get_fontweight() == ("bold" if count is not pd.NA and count else "normal")
        assert ax.get_ylim() == (0.5, -0.5)
    finally:
        plt.close(ax.figure)


def test_plot_period_shortfalls_rejects_invalid_inputs():
    index = pd.MultiIndex.from_tuples([(0, 0)], names=["day", "period"])
    table = pd.DataFrame({"Base": [-1]}, index=index)
    for limit in (0, -1, 1.5, True):
        with pytest.raises(ValueError, match="limit"):
            plot_period_shortfalls(table, limit=limit)
    with pytest.raises(ValueError, match="non-negative"):
        plot_period_shortfalls(table)
    for invalid in (table.reset_index(), table.iloc[:0]):
        with pytest.raises(ValueError, match="indexed"):
            plot_period_shortfalls(invalid)


def test_plot_period_shortfalls_uses_one_linear_scale_and_marks_tied_maxima():
    index = pd.MultiIndex.from_tuples([(3, 1), (0, 2), (1, 0)], names=["day", "period"])
    table = pd.DataFrame({"Base": [0, 2, 1], "Rush": [4, 0, 4]}, index=index)
    ax = plot_period_shortfalls(table)
    try:
        assert [label.get_fontweight() for label in ax.get_yticklabels()] == ["bold", "normal", "bold"]
        # Measure the visible bars on the same vertical level as the first track.
        segments = [segment for collection in ax.collections for segment in collection.get_segments()]
        bars = [line for line in segments if np.isclose(line[0, 1] % 1, 0.21)]
        tracks, fills = bars[::2], bars[1::2]
        ratios = []
        for track, fill in zip(tracks, fills, strict=True):
            assert track[0, 0] == fill[0, 0]
            ratios.append((fill[1, 0] - fill[0, 0]) / (track[1, 0] - track[0, 0]))
        assert ratios == pytest.approx([1.0, 0.5, 0.25, 1.0])
    finally:
        plt.close(ax.figure)


def test_plot_period_shortfalls_keeps_long_headers_separate_on_a_shared_figure():
    columns = [f"Regional campaign demand {i}" for i in range(7)]
    index = pd.MultiIndex.from_product([[0, 1], range(4)], names=["day", "period"])
    table = pd.DataFrame(np.arange(56).reshape(8, 7), columns=columns, index=index)
    table.iloc[1, 3] = np.nan
    figure, (ax, other) = plt.subplots(2, figsize=(7, 6), layout="constrained")
    try:
        assert plot_period_shortfalls(table, ax=ax) is ax
        figure.canvas.draw()
        labels = ax.get_xticklabels()
        assert [" ".join(t.get_text().split()) for t in labels] == columns
        boxes = [label.get_window_extent() for label in labels]
        assert all(a.x1 < b.x0 for a, b in zip(boxes, boxes[1:]))
        assert [text.get_text() for text in ax.texts].count("—") == 1
        assert len(ax.texts) == 56
        assert tuple(figure.get_size_inches()) == (7, 6)
        assert not other.has_data()
    finally:
        plt.close(figure)
