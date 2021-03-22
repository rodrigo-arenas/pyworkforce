from ortools.sat.python import cp_model
from pyworkforce.shifts.utils import check_positive_integer, check_positive_float


class BaseShiftScheduler:
    def __init__(self, num_days: int,
                 periods: int,
                 shifts_coverage: dict,
                 required_resources: list,
                 max_period_concurrency: int,
                 max_shift_concurrency: int,
                 max_search_time: float = 240.0,
                 num_search_workers=4):

        """
                Base class to solve the following schedule problem:

                    Its required to find the optimal number of resources (agents, operators, doctors, etc) to allocate
                    in a shift, based on a pre-defined requirement of number of resources per period of the day (periods of hours,
                    half-hour, etc)

                :param num_days: Number of days needed to schedule
                :param periods: Number of working periods in a day
                :param shifts_coverage: dict with structure {"shift_name": "shift_array"} where "shift_array" is an array of size [periods] (p), 1 if shift covers period p, 0 otherwise
                :param max_period_concurrency: Maximum resources allowed to shift in any period and day
                :param required_resources: Array of size [days, periods]
                :param max_shift_concurrency: Number of maximum allowed resources in a same shift
                :param max_search_time: Maximum time in seconds to search for a solution
                :param num_search_workers: Number of workers to search a solution
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
