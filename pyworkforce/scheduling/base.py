from ortools.sat.python import cp_model
from pyworkforce.scheduling.utils import check_positive_integer, check_positive_float


class BaseShiftScheduler:
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 max_search_time: float = 240.0,
                 num_search_workers=2):

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
        """

        is_valid_num_days = check_positive_integer("num_days", num_days)
        is_valid_periods = check_positive_integer("periods", periods)
        is_valid_max_period_concurrency = check_positive_integer("max_period_concurrency", max_period_concurrency)
        is_valid_max_shift_concurrency = check_positive_integer("max_shift_concurrency", max_shift_concurrency)
        is_valid_max_search_time = check_positive_float("max_search_time", max_search_time)
        is_valid_num_search_workers = check_positive_integer("num_search_workers", num_search_workers)

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
        self.solver = cp_model.CpSolver()
        self.transposed_shifts_coverage = None
        self.status = None
