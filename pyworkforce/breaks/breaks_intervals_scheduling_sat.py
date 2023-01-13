import math
from collections import defaultdict

from ortools.sat.python import cp_model


INTERVALS_PER_HOUR = 4

class BreaksIntervalsScheduling:
    def __init__(self,
                 num_employees: int,
                 num_intervals: int,
                 intervals_demand: list,
                 employee_calendar: dict,
                 breaks: list,
                 break_delays,
                 *args, **kwargs):

        self.num_intervals_per_day = INTERVALS_PER_HOUR * 24;
        self.num_days = int(num_intervals / self.num_intervals_per_day)

        self.num_intervals = num_intervals
        self.num_employees = num_employees
        self.employee_calendar = employee_calendar
        self.breaks = breaks
        (self.break_delays_min, self.break_delays_max) = break_delays

        self.intervals_demand = intervals_demand

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

            for (work_start_interval, work_end_interval) in self.employee_calendar[e]:

                # Accumulate intervals per working shift, order is not meaningful, hust a bag of intervals
                # It will guarantee no intervals are intersected
                working_day = []

                for (i, br) in enumerate(self.breaks):
                    (break_start_min, break_start_max, break_duration) = br
                    # breaks are relative to shift startings -> fix them:
                    break_start_min += work_start_interval
                    break_start_max += work_start_interval

                    # Break of given duration
                    start = model.NewIntVar(break_start_min, break_start_max, f'break_start_e{e}_br{i}')
                    duration = break_duration  # Python cp/sat code accepts integer variables or constants.
                    end = model.NewIntVar(work_start_interval, work_end_interval, f'break_end_e{e}_br{i}')
                    rest = model.NewIntervalVar(start, duration, end, f'break_e{e}_{i}')

                    # Working time after break, to be ensure they aren't joint
                    working_duration = model.NewIntVar(self.break_delays_min, self.break_delays_max, '')
                    working_end = model.NewIntVar(work_start_interval, work_end_interval + self.break_delays_max, '')
                    working = model.NewIntervalVar(end, working_duration, working_end, '')

                    breaks.append(
                        (start, end)
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
        solver = cp_model.CpSolver()
        solution_printer = cp_model.ObjectiveSolutionPrinter()

        status = solver.Solve(model, solution_printer)

        # Output

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print()
            print('Optimal Schedule Length: %i' % solver.ObjectiveValue())

            header0 = "Days        ";
            for d in range(self.num_days):
                # print '15' in a header
                # *4, because interval = 15 min
                header0 += f'Day {d + 1}'.rjust(INTERVALS_PER_HOUR * 24)
            print(header0)

            header = "W\\S         ";
            for i in range(self.num_days * 24):
                h = i % 24;
                header += f'{h + 1}h'.rjust(INTERVALS_PER_HOUR);
            print(header)

            #onlyRestWithoutWork = 0
            for e in range(self.num_employees):
                scheduleRow = [u'-' for _ in range(self.num_intervals)]

                for (work_start_index, work_end_index) in self.employee_calendar[e]:
                    for i in range(work_start_index, work_end_index):
                        scheduleRow[i] = u'■'

                for (break_start, break_end) in employee_rest[e]:
                    start_index = solver.Value(break_start)
                    end_index = solver.Value(break_end)
                    for i in range(start_index, end_index):
                        scheduleRow[i] = u'◊'

                scheduleRow = ''.join(scheduleRow)
                print(f'worker {e:03d}: {scheduleRow}')

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
            print(f'  - status          : {solver.StatusName(status)}')
            print(f'  - conflicts       : {solver.NumConflicts()}')
            print(f'  - branches        : {solver.NumBranches()}')
            print(f'  - booleans        : {solver.NumBooleans()}')
            print(f'  - wall time       : {solver.WallTime()} s')

        else:
            print("Solution is not feasible")
