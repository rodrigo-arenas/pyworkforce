import sys

import matplotlib
import pytest
from matplotlib import pyplot as plt

from pyworkforce.plotting import plot_coverage, plot_staffing_curve
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
