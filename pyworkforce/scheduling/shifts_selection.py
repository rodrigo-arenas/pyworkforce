import pandas as pd
from ortools.sat.python import cp_model

from pyworkforce.scheduling.base import BaseShiftScheduler


class MinAbsDifference(BaseShiftScheduler):
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 max_search_time: float = 120.0,
                 num_search_workers=2,
                 *, shift_limits=None):
        """
        Minimizes the total absolute difference between required resources per
        period and resources scheduled by the solver.

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
        max_search_time: float, default = 120
            Maximum time, in seconds, to search for a solution.
        num_search_workers: int, default = 2
            Number of workers used to search for a solution.
        shift_limits: dict, optional
            Inclusive staffing bounds by ``(day, shift_name)``.
        """

        super().__init__(num_days,
                         periods,
                         shifts_coverage,
                         required_resources,
                         max_period_concurrency,
                         max_shift_concurrency,
                         max_search_time,
                         num_search_workers,
                         shift_limits=shift_limits)

    def solve(self):
        """
        Runs the optimization solver

        Returns
        -------
        solution: dict,
            Dictionary with optimization status, scheduled resources by day and
            shift, and final objective value.
        """
        sch_model = cp_model.CpModel()

        resources = self._shift_variables(sch_model)
        gaps = []
        capacity = self.max_period_concurrency
        for day in range(self.num_days):
            for period in range(self.num_periods):
                scheduled = sum(resources[day, s] * self.shifts_coverage_matrix[s][period] for s in range(self.num_shifts))
                sch_model.Add(scheduled <= capacity)
                required = self.required_resources[day][period]
                # The largest gap occurs at one end of the feasible staffing interval.
                max_gap = max(abs(required), abs(capacity - required))
                gap = sch_model.NewIntVar(0, max_gap, f'gap_d{day}p{period}')
                sch_model.AddAbsEquality(gap, scheduled - required)
                gaps.append(gap)

        sch_model.Minimize(sum(gaps))

        self.solver.parameters.max_time_in_seconds = self.max_search_time
        self.solver.parameters.num_search_workers = self.num_search_workers

        self.status = self.solver.Solve(sch_model)

        if self.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            resources_shifts = []
            for d in range(self.num_days):
                for s in range(self.num_shifts):
                    resources_shifts.append({
                        "day": d,
                        "shift": self.shifts[s],
                        "resources": self.solver.Value(resources[d][s])})

            solution = {"status": self.solver.StatusName(self.status),
                        "cost": self.solver.ObjectiveValue(),
                        "resources_shifts": resources_shifts}
        else:
            solution = {"status": self.solver.StatusName(self.status),
                        "cost": -1,
                        "resources_shifts": [{'day': -1, 'shift': 'Unknown', 'resources': -1}]}

        return self._record_solution(solution)


class MinRequiredResources(BaseShiftScheduler):
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 cost_dict: dict = None,
                 max_search_time: float = 240.0,
                 num_search_workers: int = 2,
                 *, shift_limits=None):
        """
        Minimizes the weighted number of scheduled resources while ensuring that
        every period has at least the required number of resources.

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
        cost_dict: dict, default = None
            Dictionary of the form ``{shift: cost_value}``. It must contain the
            same shifts as ``shifts_coverage``.
        max_search_time: float, default = 240
            Maximum time, in seconds, to search for a solution.
        num_search_workers: int, default = 2
            Number of workers used to search for a solution.
        shift_limits: dict, optional
            Inclusive staffing bounds by ``(day, shift_name)``.
        """

        super().__init__(num_days,
                         periods,
                         shifts_coverage,
                         required_resources,
                         max_period_concurrency,
                         max_shift_concurrency,
                         max_search_time,
                         num_search_workers,
                         shift_limits=shift_limits)

        if cost_dict is None:
            self.cost_dict = dict.fromkeys(self.shifts, 1)
        else:
            self.cost_dict = cost_dict

        if set(sorted(self.shifts)) == set(sorted(list(self.cost_dict.keys()))):
            self.df_cost_matrix = pd.DataFrame.from_records([self.cost_dict])
        else:
            raise KeyError('cost_dict must have the same keys as shifts_coverage')

    def solve(self):
        """
        Runs the optimization solver

        Returns
        -------
        solution: dict,
            Dictionary with the status on the optimization, the resources to schedule per day and the
            final value of the cost function
        """
        sch_model = cp_model.CpModel()

        resources = self._shift_variables(sch_model)

        # Constrains

        # Total programmed resources in day d and period p, must be greater or equals that required resources in d, p
        for d in range(self.num_days):
            for p in range(self.num_periods):
                sch_model.Add(sum(resources[d][s] * self.shifts_coverage_matrix[s][p]
                                  for s in range(self.num_shifts)) >= self.required_resources[d][p])

        # Total programmed resources must be less than or equal to max_period_concurrency for each day and period
        for d in range(self.num_days):
            for p in range(self.num_periods):
                sch_model.Add(
                    sum(resources[d][s] * self.shifts_coverage_matrix[s][p]
                        for s in range(self.num_shifts)) <= self.max_period_concurrency)

        # Objective Function: Minimize the total shifted resources
        sch_model.Minimize(sum(resources[d][s] * self.df_cost_matrix[self.shifts[s]].item()
                               for d in range(self.num_days)
                               for s in range(self.num_shifts)))

        self.solver.parameters.max_time_in_seconds = self.max_search_time
        self.solver.parameters.num_search_workers = self.num_search_workers

        self.status = self.solver.Solve(sch_model)

        if self.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            resources_shifts = []
            for d in range(self.num_days):
                for s in range(self.num_shifts):
                    resources_shifts.append({
                        "day": d,
                        "shift": self.shifts[s],
                        "resources": self.solver.Value(resources[d][s])})

            solution = {"status": self.solver.StatusName(self.status),
                        "cost": self.solver.ObjectiveValue(),
                        "resources_shifts": resources_shifts}
        else:
            solution = {"status": self.solver.StatusName(self.status),
                        "cost": -1,
                        "resources_shifts": [{'day': -1, 'shift': 'Unknown', 'resources': -1}]}

        return self._record_solution(solution)
