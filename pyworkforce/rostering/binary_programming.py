import numpy as np
from ortools.sat.python import cp_model


class MinHoursRoster:
    """

    Assigns named resources to required positions by day and shift.

    The solver supports restrictions such as banned shifts, non-sequential
    shifts, rest days, and minimum working hours. It also supports soft shift
    preferences. The objective is to minimize total scheduled hours, optionally
    weighted by resource shift preferences.

    Parameters
    ----------

    num_days: int,
        Number of days to schedule.
    resources: list[str],
        Resources available to schedule.
    shifts: list,
        List of shift names.
    shifts_hours: list,
        Array of size ``[shifts]`` with the duration of each shift.
    min_working_hours: int,
        Minimum working hours per resource in the planning horizon.
    banned_shifts: list[dict]
        Each element has the form ``{"resource": resource_id, "shift": shift_name, "day": day_number}``
        and marks a shift that the resource cannot work on that day.
        example: banned_shifts": [{"resource":"e.johnston@randatmail.com", "shift": "Night", "day":  0}],
    max_resting: int,
        Maximum number of resting days per resource in the planning horizon.
    required_resources: dict[list]
        Each key must be a shift name, and each value must be a list of length
        ``num_days`` with the required resources for that shift each day.
    non_sequential_shifts: List[dict]
        Each element must have the form ``{"origin": first_shift, "destination": second_shift}``
        to prevent ``destination`` from being assigned the day after ``origin``.
        example: [{"origin":"Night", "destination":"Morning"}]
    resources_preferences: list[dict]
        Each element must have the form ``{"resource": resource_id, "shift": shift_name}``
        and indicates that the resource prefers that shift.
    resources_prioritization: list[dict], default=None
        Each element must have the form ``{"resource": resource_id, "weight": weight}``
        and represents the relative importance of that resource's preferences.
    max_search_time: float, default = 240
        Maximum time, in seconds, to search for a solution.
    num_search_workers: int, default = 2
        Number of workers used to search for a solution.
    """

    def __init__(self, num_days: int,
                 resources: list,
                 shifts: list,
                 shifts_hours: list,
                 min_working_hours: int,
                 banned_shifts: list,
                 max_resting: int,
                 required_resources: list,
                 non_sequential_shifts: list = None,
                 resources_preferences: list = None,
                 resources_prioritization: list = None,
                 max_search_time: float = 240,
                 num_search_workers=2):

        self._num_days = num_days
        self.resources = resources
        self.num_resource = len(self.resources)
        self.shifts = shifts
        self.num_shifts = len(shifts)
        self.shifts_hours = shifts_hours
        self.min_working_hours = min_working_hours
        self.banned_shifts = banned_shifts
        self.max_resting = max_resting
        self.required_resources = required_resources
        self.non_sequential_shifts = non_sequential_shifts
        self.resources_preferences = resources_preferences
        self.resources_prioritization = resources_prioritization
        self.max_search_time = max_search_time
        self.num_search_workers = num_search_workers
        self.non_sequential_shifts_indices = None
        self.resources_shifts_preferences = None
        self.resources_shifts_weight = None
        self._status = None
        self.solver = None

    def solve(self):
        """
        Runs the optimization solver

        Returns
        -------

        solution : dict,
            Dictionary that contains the status on the optimization, the list of resources to shift in each day
            and the list of resources resting for each day
        """
        sch_model = cp_model.CpModel()

        # Decision Variable

        # shifted_resource: 1 if resource n is shifted for day d in shift s
        shifted_resource = np.empty(shape=(self.num_resource, self._num_days, self.num_shifts), dtype='object')
        for n in range(self.num_resource):
            for d in range(self._num_days):
                for s in range(self.num_shifts):
                    shifted_resource[n][d][s] = sch_model.NewBoolVar(f'resource_shifts_n{n}d{d}s{s}')

        # Constrains

        # The number of scheduled resources must be greater than or equal to the requirement for each day and shift
        for d in range(self._num_days):
            for s in range(self.num_shifts):
                sch_model.Add(sum(shifted_resource[n][d][s] for n in range(self.num_resource))
                              >= self.required_resources[self.shifts[s]][d])

        # A resource can at most, work 1 shift per day
        for n in range(self.num_resource):
            for d in range(self._num_days):
                sch_model.Add(sum(shifted_resource[n][d][s] for s in range(self.num_shifts)) <= 1)

        # The number of days that an resource rest is not greater that the max allowed
        working_days = self._num_days - self.max_resting
        for n in range(self.num_resource):
            sch_model.Add(
                sum(shifted_resource[n][d][s] for d in range(self._num_days) for s in range(self.num_shifts))
                >= working_days)

        # Create bool matrix of shifts dependencies
        self.non_sequential_shifts_indices = np.zeros(shape=(self.num_shifts, self.num_shifts), dtype='object')
        if self.non_sequential_shifts:
            for dependence in self.non_sequential_shifts:
                i_idx = self.shifts.index(dependence['origin'])
                j_idx = self.shifts.index(dependence['destination'])
                self.non_sequential_shifts_indices[i_idx][j_idx] = 1

        # An resource can not have two consecutive shifts according to shifts dependencies

        for n in range(self.num_resource):
            for d in range(self._num_days - 1):
                for s in range(self.num_shifts):
                    sch_model.Add(
                        sum(shifted_resource[n][d][s] * self.non_sequential_shifts_indices[s][j] +
                            shifted_resource[n][d + 1][j]
                            for j in range(self.num_shifts)) <= 1)

        # Resources cannot be assigned to banned shifts
        if self.banned_shifts is not None:
            for ban in self.banned_shifts:
                resource_idx = self.resources.index(ban['resource'])
                shift_idx = self.shifts.index(ban['shift'])
                day_idx = int(ban['day'])
                sch_model.Add(shifted_resource[resource_idx][day_idx][shift_idx] == 0)

        # Minimum working hours per resource in the horizon

        for n in range(self.num_resource):
            sch_model.Add(
                sum(shifted_resource[n][d][s] * self.shifts_hours[s]
                    for d in range(self._num_days) for s in range(self.num_shifts)) >= self.min_working_hours)

        # resource shifts preferences

        self.resources_shifts_preferences = np.zeros(shape=(self.num_resource, self.num_shifts), dtype='object')

        if self.resources_preferences:
            for preference in self.resources_preferences:
                resource_idx = self.resources.index(preference['resource'])
                shift_idx = self.shifts.index(preference['shift'])
                self.resources_shifts_preferences[resource_idx][shift_idx] = 1

        # resource relative weight for shift preferences
        self.resources_shifts_weight = np.ones(shape=self.num_resource, dtype='object')
        if self.resources_prioritization:
            for prioritization in self.resources_prioritization:
                resource_idx = self.resources.index(prioritization['resource'])
                self.resources_shifts_weight[resource_idx] = prioritization['weight']

        # Objective function: Minimize the total number of shifted hours rewarded by resource preferences

        sch_model.Minimize(
            sum(shifted_resource[n][d][s] * (self.shifts_hours[s]
                                             - self.resources_shifts_weight[n] *
                                             self.resources_shifts_preferences[n][s])
                for n in range(self.num_resource)
                for d in range(self._num_days)
                for s in range(self.num_shifts)))

        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.max_search_time
        self.solver.num_search_workers = self.num_search_workers

        self._status = self.solver.Solve(sch_model)

        # Output

        if self._status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            resource_shifts = []
            resting_resource = []
            shifted_hours = 0
            for n in range(self.num_resource):
                for d in range(self._num_days):
                    working = False
                    for s in range(self.num_shifts):
                        if self.solver.Value(shifted_resource[n][d][s]):
                            resource_shifts.append({
                                "resource": self.resources[n],
                                "day": d,
                                "shift": self.shifts[s]})
                            working = True
                            shifted_hours += self.shifts_hours[s]
                    if not working:
                        resting_resource.append({
                            "resource": self.resources[n],
                            "day": d
                        })

            solution = {"status": self.solver.StatusName(self._status),
                        "cost": self.solver.ObjectiveValue(),
                        "shifted_hours": shifted_hours,
                        "total_resources": len(self.resources),
                        "total_shifts": len(resource_shifts),
                        "resting_days": len(resting_resource),
                        "resource_shifts": resource_shifts,
                        "resting_resource": resting_resource}
        else:
            solution = {"status": self.solver.StatusName(self._status),
                        "cost": -1,
                        "shifted_hours": -1,
                        "total_resources": 0,
                        "total_shifts": 0,
                        "resting_days": 0,
                        "resource_shifts": [{'resource': -1, 'day': -1, 'shift': 'Unknown'}],
                        "resting_resource": [{'resource': -1, 'day': -1}]}

        return solution
