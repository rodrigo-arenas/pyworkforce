from collections.abc import Mapping
from numbers import Integral

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from pyworkforce.base import BaseWorkforce
from pyworkforce.utils._cp_sat import method
from pyworkforce.utils.validation import check_positive_float, check_positive_integer


class BaseShiftScheduler(BaseWorkforce):
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 max_search_time: float = 240.0,
                 num_search_workers=2,
                 *, shift_limits=None):

        """
        Base class for shift scheduling problems.

        Scheduling finds the number of resources (agents, operators, doctors, etc.)
        to allocate to each shift, based on predefined resource requirements by
        period of the day.

        Parameters
        ----------

        num_days: int,
            Number of days to schedule.
        periods: int,
            Number of working periods in a day.
        shifts_coverage: dict,
            Dictionary of the form ``{"shift_name": shift_array}``, where each
            ``shift_array`` has length ``periods`` and uses 1 when the shift
            covers a period, otherwise 0.
        required_resources: list,
            Array of size ``[days, periods]``.
        max_period_concurrency: int,
            Maximum resources allowed in any period and day.
        max_shift_concurrency: int,
            Maximum resources allowed in the same shift.
        max_search_time: float, default = 240
            Maximum time, in seconds, to search for a solution.
        num_search_workers: int, default = 2
            Number of workers used to search for a solution.
        shift_limits: dict, optional
            Map ``(day, shift_name)`` to inclusive ``(minimum, maximum)`` staffing
            limits. Days start at zero. Unspecified shifts use the global limits.

        Attributes
        ----------
        solution_: dict or None,
            The last solution returned by :meth:`solve`. ``None`` until solved.
        """

        check_positive_integer("num_days", num_days)
        check_positive_integer("periods", periods)
        check_positive_integer("max_period_concurrency", max_period_concurrency)
        check_positive_integer("max_shift_concurrency", max_shift_concurrency)
        check_positive_float("max_search_time", max_search_time)
        check_positive_integer("num_search_workers", num_search_workers)

        if not isinstance(shifts_coverage, dict) or len(shifts_coverage) == 0:
            raise ValueError("shifts_coverage must be a non-empty dictionary "
                             "of {shift_name: coverage_array}")

        for shift_name, coverage in shifts_coverage.items():
            if len(coverage) != periods:
                raise ValueError(
                    f"shifts_coverage['{shift_name}'] has length {len(coverage)}, "
                    f"but 'periods' is {periods}; every coverage array must have "
                    f"exactly 'periods' entries")

        if len(required_resources) != num_days:
            raise ValueError(
                f"required_resources has {len(required_resources)} rows, but "
                f"'num_days' is {num_days}; it must be an array of shape [num_days, periods]")

        for day, day_resources in enumerate(required_resources):
            if len(day_resources) != periods:
                raise ValueError(
                    f"required_resources[{day}] has length {len(day_resources)}, "
                    f"but 'periods' is {periods}; it must be an array of shape "
                    f"[num_days, periods]")

        self.num_days = num_days
        self.periods = periods
        self.shifts_coverage = shifts_coverage
        self.shifts = list(shifts_coverage.keys())
        self.num_shifts = len(self.shifts)
        self.num_periods = periods
        self.shifts_coverage_matrix = list(shifts_coverage.values())
        self.max_shift_concurrency = max_shift_concurrency
        self.max_period_concurrency = max_period_concurrency
        self.required_resources = required_resources
        self.max_search_time = max_search_time
        self.num_search_workers = num_search_workers
        self.shift_limits = shift_limits
        if shift_limits is not None:
            self._validate_shift_limits(shift_limits)
        self.solver = cp_model.CpSolver()
        self.transposed_shifts_coverage = None
        self.status = None
        self.solution_ = None
        self._solved_plan = None
        self._last_status = None

    def _validate_shift_limits(self, limits):
        if not isinstance(limits, Mapping):
            raise ValueError("shift_limits must map (day, shift_name) to (minimum, maximum)")
        for key, bounds in limits.items():
            if not isinstance(key, tuple) or len(key) != 2:
                raise ValueError(f"shift_limits contains an invalid (day, shift_name): {key!r}")
            day, shift = key
            if isinstance(day, bool) or not isinstance(day, Integral) or not 0 <= day < self.num_days or shift not in self.shifts:
                raise ValueError(f"shift_limits contains an invalid (day, shift_name): {key!r}")
            if (
                not isinstance(bounds, (tuple, list)) or len(bounds) != 2
                or any(isinstance(n, bool) or not isinstance(n, Integral) for n in bounds)
                or not 0 <= bounds[0] <= bounds[1] <= self.max_shift_concurrency
            ):
                raise ValueError(f"shift_limits[{key!r}] must satisfy 0 <= minimum <= maximum <= max_shift_concurrency")

    def _shift_variables(self, model):
        limits = self.shift_limits if self.shift_limits is not None else {}
        self._validate_shift_limits(limits)
        resources = np.empty((self.num_days, self.num_shifts), dtype=object)
        for day in range(self.num_days):
            for index, shift in enumerate(self.shifts):
                lower, upper = limits.get((day, shift), (0, self.max_shift_concurrency))
                resources[day, index] = method(model, "new_int_var")(lower, upper, f"resources_d{day}s{index}")
        return resources

    def _record_solution(self, solution):
        status = solution["status"]
        self._solved_plan = None
        if status in ("OPTIMAL", "FEASIBLE"):
            resources = {shift: [0] * self.num_days for shift in self.shifts}
            for row in solution["resources_shifts"]:
                resources[row["shift"]][row["day"]] = row["resources"]
            self._solved_plan = (
                np.array(self.required_resources, dtype=object),
                np.array(self.shifts_coverage_matrix, dtype=np.int64),
                resources,
            )
        self._last_status = status
        self.solution_ = solution
        return solution

    def _require_plan(self):
        if self._last_status is None:
            raise RuntimeError("Call solve() before requesting scheduled resources")
        if self._solved_plan is None:
            raise RuntimeError(f"The last solve has no schedule to inspect: {self._last_status}")
        return self._solved_plan

    def scheduled_resources(self):
        """Return ``{shift_name: [headcount_day_0, ...]}`` from the last solve.

        The returned mapping can be passed to ``BreakScheduler``. Raises
        ``RuntimeError`` before a solve or when the last solve has no plan.
        """
        _, _, resources = self._require_plan()
        return {shift: counts.copy() for shift, counts in resources.items()}

    def coverage(self, required_resources=None):
        """Return one row per day and period, with demand, staffing and coverage gaps.

        Pass alternate demand of shape ``(num_days, periods)`` to evaluate the
        same schedule without re-optimizing. Use non-negative 64-bit integers.
        ``shortfall`` and ``surplus`` are reported separately in headcount units.
        """
        original, shift_coverage, resources = self._require_plan()
        num_days, periods = original.shape
        demand = original if required_resources is None else np.asarray(required_resources, dtype=object)
        max_count = np.iinfo(np.int64).max
        if demand.shape != original.shape or any(
            isinstance(n, bool) or not isinstance(n, Integral) or not 0 <= n <= max_count for n in demand.flat
        ):
            raise ValueError("required_resources must match the solved shape and contain non-negative 64-bit integers")

        scheduled = np.asarray(list(resources.values())).T @ shift_coverage
        required = demand.astype(np.int64).ravel()
        scheduled = scheduled.astype(np.int64).ravel()
        gap = scheduled - required
        return pd.DataFrame({
            "day": np.repeat(np.arange(num_days), periods),
            "period": np.tile(np.arange(periods), num_days),
            "required": required,
            "scheduled": scheduled,
            "shortfall": np.maximum(-gap, 0),
            "surplus": np.maximum(gap, 0),
        })

    def compare_coverage(self, scenarios, *, by_period=False):
        """Summarize one solved plan against a non-empty mapping of named demand scenarios.

        Use ``None`` for original demand. Required, scheduled, shortfall and
        surplus totals are person-periods. With ``by_period=True``, return shortfall
        headcounts indexed by (day, period), with scenarios in mapping order.
        The largest shortfall in any scenario ranks first, with ties in
        chronological order. Covered intervals are included.
        """
        if not isinstance(scenarios, Mapping) or not scenarios:
            raise ValueError("scenarios must be a non-empty mapping of names to demand arrays")
        frames = ((name, self.coverage(demand)) for name, demand in scenarios.items())
        if by_period:
            shortfalls = [frame.set_index(["day", "period"])["shortfall"] for _, frame in frames]
            table = pd.concat(shortfalls, axis=1)
            table.columns = pd.Index(scenarios, name="scenario", tupleize_cols=False)
            priority = table.max(axis=1).sort_values(ascending=False, kind="stable")
            return table.loc[priority.index]

        rows = []
        for scenario, coverage in frames:
            totals = {column: sum(map(int, coverage[column])) for column in ("required", "scheduled", "shortfall", "surplus")}
            rows.append({"scenario": scenario, **totals, "understaffed_periods": (coverage["shortfall"] > 0).sum()})
        return pd.DataFrame(rows)
