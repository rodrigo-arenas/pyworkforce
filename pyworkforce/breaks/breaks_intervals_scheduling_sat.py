import math
from collections import defaultdict

from ortools.sat.python import cp_model


INTERVALS_PER_HOUR = 4

class BreaksIntervalsScheduling:
    def __init__(self,
                 # intervals_demand: list, # not used for the moment
                 employee_calendar: dict,
                 breaks: list,
                 break_min_delay: int,
                 break_max_delay: int,
                 *args, **kwargs):

        self.employee_calendar = employee_calendar
        self.breaks = breaks
        self.break_min_delay = break_min_delay
        self.break_max_delay = break_max_delay

        # not using it now
        # self.intervals_demand = intervals_demand

        self.solver = None
        self.status = None

    def solve(self):

        """Solves the shift scheduling problem."""

        print("Model building...")

        model = cp_model.CpModel()

        # Linear terms of the objective in a minimization context.
        # obj_int_vars = []
        # obj_int_coeffs = []
        # obj_bool_vars = []
        # obj_bool_coeffs = []

        # 1. Remember employees' rest/breaks intervals
        # Will use it to get results per employee
        employee_rest = {}

        for e in self.employee_calendar:
            breaks = []

            for (shift_day_num, day_work_start_interval, day_work_end_interval) in self.employee_calendar[e]:

                # Accumulate intervals per working shift, order is not meaningful, hust a bag of intervals
                # It will guarantee no intervals are intersected
                working_day = []

                for (i, br) in enumerate(self.breaks):
                    (_id, break_start_min, break_start_max, break_duration) = br
                    # breaks are relative to shift startings -> fix them:
                    break_start_min += day_work_start_interval
                    break_start_max += day_work_start_interval

                    # Break of given duration
                    start = model.NewIntVar(break_start_min, break_start_max, f'break_start_e{e}_br{i}')
                    duration = break_duration  # Python cp/sat code accepts integer variables or constants.
                    end = model.NewIntVar(day_work_start_interval, day_work_end_interval, f'break_end_e{e}_br{i}')
                    rest = model.NewIntervalVar(start, duration, end, f'break_e{e}_{i}')

                    # Working time after break, to be ensure they aren't joint
                    working_duration = model.NewIntVar(self.break_min_delay, self.break_max_delay, '')
                    working_end = model.NewIntVar(day_work_start_interval, day_work_end_interval + self.break_max_delay, '')
                    working = model.NewIntervalVar(end, working_duration, working_end, '')

                    breaks.append(
                        (shift_day_num, _id, start, end)
                    )

                    working_day.extend(
                        [rest, working]
                    )


                # This will require no overlaps of intervals during the shift.
                # Hence, will have a form ideally:
                #
                # employee calendar : ------------------■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■------------------
                # assigned breaks   : ------------------wwwwbwwwwwwwbbwwwwwwwwwwwwbwwwwwwwww------------------
                model.AddNoOverlap(working_day)

            # Remember what breaks were assigned to worker per shift
            employee_rest[e] = breaks


        # Objective
        # model.Minimize(
        #     sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars))) +
        #     sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars)))
        # )

        # print(f'Model bool vars: {len(obj_bool_vars)}')
        # print(f'Model int vars: {len(obj_int_vars)}')

        print("Solving started...")

        # Solve the model.
        self.solver = cp_model.CpSolver()
        solution_printer = cp_model.ObjectiveSolutionPrinter()

        self.status = self.solver.Solve(model, solution_printer)

        # Output

        solution = {}
        if self.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            scheduled_breaks = {}

            for e in self.employee_calendar.keys():
                emp_breaks = []
                for (shift_day_num, break_id, break_start, break_end) in employee_rest[e]:
                    start_index = self.solver.Value(break_start)
                    end_index = self.solver.Value(break_end)

                    emp_breaks.append(
                        (shift_day_num, break_id, start_index, end_index)
                    )

                scheduled_breaks[e] = emp_breaks

            solution = {
                "status": self.solver.StatusName(self.status),
                "cost": self.solver.ObjectiveValue(),
                "num_branches": self.solver.NumBranches(),
                "num_conflicts": self.solver.NumConflicts(),
                "wall_time": self.solver.WallTime(),
                "num_resources": len(self.employee_calendar),
                "resource_break_intervals": scheduled_breaks,
            }

        else:
            solution = {
                "status": self.solver.StatusName(self.status),
                "cost": -1,
                "num_branches": -1,
                "num_conflicts": -1,
                "wall_time": -1,
                "num_resources": len(self.employee_calendar.keys()),
                "resource_break_intervals": {},
            }

        return solution
