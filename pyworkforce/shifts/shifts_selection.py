import numpy as np
from ortools.sat.python import cp_model


class MinAbsDifference:
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int = None,
                 max_shift_concurrency: int = None,
                 max_search_time: float = 120,
                 num_search_workers=4,
                 *args, **kwargs):
        """
        Solves the following schedule problem:

            Its required to find the optimal number of resources (agents, operators, doctors, etc) to allocate
            in a shift, based on a pre-defined requirement of # of resources per period of the day (periods of hours,
            half-hour, etc)

            The optimal criteria, is defined as the amount of resources per shifts that minimize the total absolute
            difference, between the required resources per period and the actual shifted by the solver


        :param num_days: Number of days needed to schedule
        :param periods: Number of working periods in a day
        :param shifts_coverage: dict with structure {"shift_name": "shift_array"} where "shift_array" is an array
        of size [periods] (p), 1 if shift covers period p, 0 otherwise
        :param max_period_concurrency: Maximum resources allowed to shift in any period and day
        :param required_resources: Array of size [days, periods]
        :param max_shift_concurrency: Number of maximum allowed resources in a same shift
        :param max_search_time: Maximum time in seconds to search for a solution
        :param num_search_workers: Number of workers to search a solution
        """

        self.num_days = num_days
        self.shifts = list(shifts_coverage.keys())
        self.num_shifts = len(self.shifts)
        self.num_periods = periods
        self.shifts_coverage_matrix = list(shifts_coverage.values())
        self.max_shift_concurrency = max_shift_concurrency
        self.max_period_concurrency = max_period_concurrency
        self.required_resources = required_resources
        self.max_search_time = max_search_time
        self.num_search_workers = num_search_workers
        self.transposed_shifts_coverage = None
        self.status = None
        self.solver = None

    def solve(self):
        sch_model = cp_model.CpModel()

        # Resources: Number of resources assigned in day d to shift s
        resources = np.empty(shape=(self.num_days, self.num_shifts), dtype='object')
        # transition resources: Variable to change domain coordinates from min |x-a|
        # to min t, s.t t>= x-a and t>= a-x
        transition_resources = np.empty(shape=(self.num_days, self.num_periods), dtype='object')

        # Resources
        if self.max_shift_concurrency is not None:
            for d in range(self.num_days):
                for s in range(self.num_shifts):
                    resources[d][s] = sch_model.NewIntVar(0, self.max_shift_concurrency, f'agents_d{d}s{s}')

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
                sch_model.Add(sum(resources[d][s] * self.shifts_coverage_matrix[s][p] for s in range(self.num_shifts)) <=
                              self.max_period_concurrency)

        # Objective Function: Minimize the absolute value of the difference between required and shifted resources

        sch_model.Minimize(
            sum(transition_resources[d][p] for d in range(self.num_days) for p in range(self.num_periods)))

        self.solver = cp_model.CpSolver()
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
