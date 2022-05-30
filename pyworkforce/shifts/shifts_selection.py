import numpy as np
import pandas as pd
from ortools.sat.python import cp_model
from pyworkforce.shifts.base import BaseShiftScheduler


class MinAbsDifference(BaseShiftScheduler):
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 max_search_time: float = 120.0,
                 num_search_workers=2,
                 *args, **kwargs):
        """
        The "optimal" criteria is defined as the number of resources per shift
        that minimize the total absolute difference between the required resources
        per period and the actual shifts found by the solver

        Parameters
        ----------

        num_days: int,
            Number of days needed to schedule
        periods: int,
            Number of working periods in a day
        shifts_coverage: dict,
            dict with structure {"shift_name": "shift_array"} where "shift_array" is an array of size [periods] (p), 1 if shift covers period p, 0 otherwise
        required_resources: list,
            Array of size [days, periods]
        max_period_concurrency: int,
            Maximum resources that are allowed to shift in any period and day
        max_shift_concurrency: int,
            Number of maximum allowed resources in the same shift
        max_search_time: float, default = 240
            Maximum time in seconds to search for a solution
        num_search_workers: int, default = 2
            Number of workers to search for a solution
        """

        super().__init__(num_days,
                         periods,
                         shifts_coverage,
                         required_resources,
                         max_period_concurrency,
                         max_shift_concurrency,
                         max_search_time,
                         num_search_workers)

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

        # Resources: Number of resources assigned in day d to shift s
        resources = np.empty(shape=(self.num_days, self.num_shifts), dtype='object')
        # transition resources: Variable to change domain coordinates from min |x-a|
        # to min t, s.t t>= x-a and t>= a-x
        transition_resources = np.empty(shape=(self.num_days, self.num_periods), dtype='object')

        # Resources
        for d in range(self.num_days):
            for s in range(self.num_shifts):
                resources[d][s] = sch_model.NewIntVar(0, self.max_shift_concurrency, f'resources_d{d}s{s}')

        for d in range(self.num_days):
            for p in range(self.num_periods):
                transition_resources[d][p] = sch_model.NewIntVar(-self.max_period_concurrency,
                                                                 self.max_period_concurrency,
                                                                 f'transition_resources_d{d}p{p}')

        # Constrains

        # transition must be between x-a and a-x
        for d in range(self.num_days):
            for p in range(self.num_periods):
                sch_model.Add(transition_resources[d][p] >= (
                        sum(resources[d][s] * self.shifts_coverage_matrix[s][p] for s in range(self.num_shifts)) -
                        self.required_resources[d][p]))
                sch_model.Add(transition_resources[d][p] >= (self.required_resources[d][p]
                                                             - sum(resources[d][s] * self.shifts_coverage_matrix[s][p]
                                                                   for s in range(self.num_shifts))))

        # Total programmed resources, must be less or equals to max_period_concurrency, for each day and period
        for d in range(self.num_days):
            for p in range(self.num_periods):
                sch_model.Add(
                    sum(resources[d][s] * self.shifts_coverage_matrix[s][p] for s in range(self.num_shifts)) <=
                    self.max_period_concurrency)

        # Objective Function: Minimize the absolute value of the difference between required and shifted resources

        sch_model.Minimize(
            sum(transition_resources[d][p] for d in range(self.num_days) for p in range(self.num_periods)))

        self.solver.parameters.max_time_in_seconds = self.max_search_time
        self.solver.num_search_workers = self.num_search_workers

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

        return solution


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
                 *args, **kwargs):
        """
        The "optimal" criteria is defined as the minimum weighted amount
        of resources (by optional shift cost), that ensures that there are never
        fewer resources shifted than the ones required per period

        Parameters
        ----------

        num_days: int,
            Number of days needed to schedule
        periods: int,
            Number of working periods in a day
        shifts_coverage: dict,
            dict with structure {"shift_name": "shift_array"} where "shift_array" is an array of size [periods] (p), 1 if shift covers period p, 0 otherwise
        required_resources: list,
            Array of size [days, periods]
        max_period_concurrency: int,
            Maximum resources that are allowed to shift in any period and day
        max_shift_concurrency: int,
            Number of maximum allowed resources in the same shift
        cost_dict: dict, default = None
            dictionary of form {shift: cost_value}, where shift must be the same options listed in the
            shifts_coverage matrix, and they must be all integers
        max_search_time: float, default = 240
            Maximum time in seconds to search for a solution
        num_search_workers: int, default = 2
            Number of workers to search for a solution
        """

        super().__init__(num_days,
                         periods,
                         shifts_coverage,
                         required_resources,
                         max_period_concurrency,
                         max_shift_concurrency,
                         max_search_time,
                         num_search_workers)

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

        # Resources: Number of resources assigned in day d to shift s
        resources = np.empty(shape=(self.num_days, self.num_shifts), dtype='object')

        # Resources
        for d in range(self.num_days):
            for s in range(self.num_shifts):
                resources[d][s] = sch_model.NewIntVar(0, self.max_shift_concurrency, f'resources_d{d}s{s}')

        # Constrains

        # Total programmed resources in day d and period p, must be greater or equals that required resources in d, p
        for d in range(self.num_days):
            for p in range(self.num_periods):
                sch_model.Add(sum(resources[d][s] * self.shifts_coverage_matrix[s][p]
                                  for s in range(self.num_shifts)) >= self.required_resources[d][p])

        # Total programmed resources, must be less or equals to max_period_concurrency, for each day and period
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
        self.solver.num_search_workers = self.num_search_workers

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

        return solution
