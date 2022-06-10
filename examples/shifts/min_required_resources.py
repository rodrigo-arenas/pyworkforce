"""
Requirement: Find the number of workers needed to schedule per shift in a production plant for the next 2 days with the
    following conditions:
    * There is a number of required persons per hour and day given in the matrix "required_resources"
    * There are 4 available shifts called "Morning", "Afternoon", "Night", "Mixed"; their start and end hour is
      determined in the dictionary "shifts_coverage", 1 meaning the shift is active at that hour, 0 otherwise
    * The number of required workers per day and period (hour) is determined in the matrix "required_resources"
    * The maximum number of workers that can be shifted simultaneously at any hour is 25, due plat capacity restrictions
    * The maximum number of workers that can be shifted in a same shift, is 20
"""

from pyworkforce.shifts import MinRequiredResources
from pprint import PrettyPrinter

# Columns are an hour of the day, rows are the days
# N_dp
required_resources = [
    [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
    [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
]

# Each entry of a shift, is an hour of the day (24 columns)
# E_sp
shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                   "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                   "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

# The cost of shifting a resource if each shift, if present, solver will minimize the total cost
# C_s
cost_dict = {"Morning": 1, "Afternoon": 1.2, "Night": 2, "Mixed": 1.5}

scheduler = MinRequiredResources(num_days=2,  # S
                                 periods=24,  # P
                                 shifts_coverage=shifts_coverage,
                                 required_resources=required_resources,
                                 max_period_concurrency=27,  # gamma
                                 max_shift_concurrency=25)   # beta

solution = scheduler.solve()
pp = PrettyPrinter(indent=2)
pp.pprint(solution)
