from ortools.sat.python import cp_model

def main():

    # init model
    model = cp_model.CpModel()

    num_employees = 3
    num_intervals = 24

    # (employee_num, min_start, max_end)
    employee_preferences = [
        (0, 0, 14),  # lets say emp0 works mornings (till 14:00)
        (2, 11, 0)   # and emp2 works evenings (starting from 11:00)
    ]

    # overlaps [e, i] -> employees x intervals
    overlaps = {}

    expected_amount = 2

    emp_intervalvars = []
    for e in range(num_employees):
        start = model.NewIntVar(0, num_intervals, f'start_e{e}')
        end = model.NewIntVar(0, num_intervals, f'end_e{e}')
        dur = model.NewIntVar(0, 9, f'duration_e{e}') # no more than 9hrs of work
        pres = model.NewBoolVar(f'presence_e{e}')
        interval = model.NewOptionalIntervalVar(start, dur, end, pres, f'interval_e{e}')

        # calc start
        model.Add(start == (end - dur)).OnlyEnforceIf(pres)

        # make sure to set start/end to 0 if not present
        model.Add(dur == 0).OnlyEnforceIf(pres.Not())
        model.Add(start == 0).OnlyEnforceIf(pres.Not())
        model.Add(end == 0).OnlyEnforceIf(pres.Not())

        # make sure to set start/duration to > 0 if present
        model.Add(dur > 0).OnlyEnforceIf(pres)
        model.Add(end > 0).OnlyEnforceIf(pres)

        # all emps between 8am and 6pm
        model.Add(start >= 8).OnlyEnforceIf(pres)
        model.Add(end <= 21).OnlyEnforceIf(pres)

        # 1. Apply employee preferences
        for ep in employee_preferences:
            (employee_num, min_start, max_end) = ep
            if e != employee_num:
                continue

            if min_start > 0:
                model.Add(start >= min_start)
            if max_end > 0:
                model.Add(end <= max_end)

        # 2. Create overlap matrix to print hours later
        for i in range(24):
            # l. perron solution
            overlap_i = model.NewBoolVar(f'overlap_e{e}_i{i}')
            before_i = model.NewBoolVar(f'before_e{e}_i{i}')
            after_i = model.NewBoolVar(f'after_e{e}_i{i}')

            model.Add(start <= i).OnlyEnforceIf(overlap_i)
            model.Add(end > i).OnlyEnforceIf(overlap_i)  # Intervals are open ended on the right

            model.Add(end <= i).OnlyEnforceIf(before_i)
            model.Add(start > i).OnlyEnforceIf(after_i)

            model.Add(overlap_i + before_i + after_i == 1)
            overlaps[e, i] = overlap_i
            # l. perron solution - end

        emp_intervalvars.append({
            "present": pres,
            "start": start,
            "end": end,
            "duration": dur,
            "interval": interval
        })

    # simple objective - maximize durartions
    durations = list(map(lambda v: v["duration"], emp_intervalvars))
    model.Maximize(sum(durations))

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress=True
    status = solver.Solve(model)
    print(solver.StatusName(status))

    for i,field in enumerate(model._CpModel__model.variables):
        if field.name == '':
            continue
        print("{} : {}".format(field.name,solver._CpSolver__solution.solution[i]))

    # Print solution
    for e in range(num_employees):
        row = ''
        for i in range(num_intervals):
            if solver.BooleanValue(overlaps[e, i]):
                row += u' ■ '
            else:
                row += u' □ '

        print(f'Emp {e}: {row}')


if __name__ == '__main__':
    main()