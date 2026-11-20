import sys

import matplotlib
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
        assert ax.images[0].get_clim() == (0, 3)
        assert ax.images[0].get_array().mask.tolist() == [[False, False, True]]
    finally:
        plt.close(figure)


@pytest.mark.parametrize(("count", "label"), [(0, "0"), (pd.NA, "—"), (2**53 + 1, str(2**53 + 1))])
def test_plot_period_shortfalls_single_interval_and_exact_annotation(count, label):
    index = pd.MultiIndex.from_tuples([(0, 0)], names=["day", "period"])
    table = pd.DataFrame({"Base": pd.array([count], dtype="Int64")}, index=index)
    ax = plot_period_shortfalls(table)
    try:
        assert [text.get_text() for text in ax.texts] == [label]
        assert ax.images[0].get_clim()[1] >= 1
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
