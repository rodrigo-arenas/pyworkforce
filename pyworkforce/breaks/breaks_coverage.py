
def calculate_coverage (schedule, total_intervals):
    # schedule:
    # 'emp' -> [(shift_day_num, work_start_interval, work_end_interval)]

    coverage = [0 for _ in range(total_intervals)]

    for _, employee_calendar in schedule.items():
        for (day_num, start, end) in employee_calendar:
            coverage[start:end] = [c+1 for c in coverage[start:end]]

    return coverage