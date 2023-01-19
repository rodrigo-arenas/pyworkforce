from collections import defaultdict

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpSolver

from pyworkforce.breaks.breaks_intervals_scheduling_sat import BreaksIntervalsScheduling


class BreaksPrinter:
    def __init__(self,
                 num_intervals: int,
                 intervals_per_hour: int,
                 employee_calendar: dict,
                 solution: any,
                 break_symbols: dict = {},
                 *args, **kwargs):

        self.intervals_per_hour = intervals_per_hour
        self.num_intervals_per_day = self.intervals_per_hour * 24;
        self.num_intervals = num_intervals
        self.num_days = int(num_intervals / self.num_intervals_per_day)

        self.num_intervals = num_intervals
        self.num_employees = len(employee_calendar)
        self.employee_calendar = employee_calendar

        if len(break_symbols) > 0:
            self.break_symbols = break_symbols
        else:
            self.break_symbols = defaultdict(u'◊')

        self.solution = solution

    def print(self):

        if self.solution["status"] in ["OPTIMAL", "FEASIBLE"]:
            print()
            print('Cost: %i' % self.solution["cost"])

            header0 = "Days        ";
            for d in range(self.num_days):
                # print '15' in a header
                # *4, because interval = 15 min
                header0 += f'Day {d + 1}'.rjust(self.intervals_per_hour * 24)
            print(header0)

            header = "W\\S         ";
            for i in range(self.num_days * 24):
                h = i % 24;
                header += f'{h + 1}h'.rjust(self.intervals_per_hour);
            print(header)

            #onlyRestWithoutWork = 0
            for e in range(self.num_employees):
                schedule_row = [u'-' for _ in range(self.num_intervals)]

                for (work_start_index, work_end_index) in self.employee_calendar[e]:
                    for i in range(work_start_index, work_end_index):
                        schedule_row[i] = u'■'

                for (picture_id, break_start, break_end) in self.solution["resource_breaks"][e]:
                    for i in range(break_start, break_end):
                        schedule_row[i] = self.break_symbols[picture_id]

                schedule_row = ''.join(schedule_row)
                print(f'worker {e:03d}: {schedule_row}')

            #print(f"Only rest, without work: {onlyRestWithoutWork}")
            # print('Penalties:')
            # for i, var in enumerate(obj_bool_vars):
            #     if solver.BooleanValue(var):
            #         penalty = obj_bool_coeffs[i]
            #         if penalty > 0:
            #             print(f'  {var.Name()} violated, penalty={penalty}')
            #         else:
            #             print(f'  {var.Name()} fulfilled, gain={-penalty}')

            # for i, var in enumerate(obj_int_vars):
            #     if solver.Value(var) > 0:
            #         print(f'  {var.Name()} violated by {solver.Value(var)}, linear penalty={obj_int_coeffs[i]}')

            print()
            print('Statistics')
            print(f'  - status          : {self.solution["status"]}')
            print(f'  - conflicts       : {self.solution["num_conflicts"]}')
            print(f'  - branches        : {self.solution["num_branches"]}')
            print(f'  - wall time       : {self.solution["wall_time"]} s')

        else:
            print("Solution is not feasible")