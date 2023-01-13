from random import randrange
from pyworkforce.breaks.breaks_intervals_scheduling_sat import BreaksIntervalsScheduling


def get_12h_break_config():
    _1h_interval = int(1 * 60 / 15)
    _30m = 2

    _12_h_breaks = [
        # 1st lunch break: 03:00 -> 05:30, 30min
        (3 * _1h_interval, 5 * _1h_interval + _30m, 2),

        # 2nd lunch break: 05:30 -> 09:30, 30min
        (5 * _1h_interval + _30m, 9 * _1h_interval, 2),

        # just break: 05:30 -> 11:00, 15min
        (5 * _1h_interval + _30m, 11 * _1h_interval, 1),

        # just break: 01:00 -> 10:00, 15min
        (1 * _1h_interval, 10 * _1h_interval, 1),
    ]
    return _12_h_breaks


def generate_12h_calendar(num_days, num_workers):

    _1h_interval = int(1 * 60 / 15)
    _12h_intervals = 12 * _1h_interval
    _1d_intervals = 24 * _1h_interval

    schedule = {}

    for w in range(num_workers):
        _start = randrange(6*_1h_interval, 12*_1h_interval)
        schedule[w] = [ (d * _1d_intervals + _start, d * _1d_intervals + _start + 12 * _1h_interval) for d in range(num_days)]

    return schedule


def test_1_day_3_employee():
    _days = 1
    _1h_interval = int(1 * 60 / 15)
    _12h_intervals = 12*_1h_interval
    _1d_intervals = 24 * _1h_interval
    _30m = 2

    # employee shifts
    calendar = generate_12h_calendar(num_workers=1, num_days=_days)

    # Configuration of breaks
    # 1. Delays between breaks
    min_break_delay = int(1.5 * _1h_interval)
    max_break_delay = int(3.5 * _1h_interval)

    # 2. Break rules
    #    (min_start, max_start, duration)
    _12_h_breaks = get_12h_break_config()

    model = BreaksIntervalsScheduling(
        num_employees=1,
        num_intervals=_1d_intervals * _days,
        intervals_demand=[1 for _ in range(_1d_intervals * _days)],
        employee_calendar=calendar,
        breaks=_12_h_breaks,
        break_delays=(min_break_delay, max_break_delay)
    )

    model.solve()


def test_1_week_3_employee():
    _days = 7
    _1h_interval = int(1 * 60 / 15)
    _9h_intervals = 9*_1h_interval
    _1d_intervals = 24 * _1h_interval

    # employee shifts
    calendar = generate_12h_calendar(_days, 3)

    # Configuration of breaks
    # 1. Delays between breaks
    min_break_delay = int(1.5 * _1h_interval)
    max_break_delay = int(3.5 * _1h_interval)

    # 2. Break rules
    #    (min_start, max_start, duration)
    _12_h_breaks = get_12h_break_config()

    model = BreaksIntervalsScheduling(
        num_employees=len(calendar),
        num_intervals=_1d_intervals * _days,
        intervals_demand=[1 for _ in range(_1d_intervals * _days)],  # not used
        employee_calendar=calendar,
        breaks=_12_h_breaks,
        break_delays=(min_break_delay, max_break_delay)
    )

    model.solve()

def test_1_week_100_employee():
    _days = 7
    _1h_interval = int(1 * 60 / 15)
    _9h_intervals = 9 * _1h_interval
    _1d_intervals = 24 * _1h_interval

    # employee shifts
    calendar = generate_12h_calendar(_days, 100)

    # Configuration of breaks
    # 1. Delays between breaks
    min_break_delay = int(1.5 * _1h_interval)
    max_break_delay = int(3.5 * _1h_interval)

    # 2. Break rules
    #    (min_start, max_start, duration)
    _12_h_breaks = get_12h_break_config()

    model = BreaksIntervalsScheduling(
        num_employees=len(calendar),
        num_intervals=_1d_intervals * _days,
        intervals_demand=[1 for _ in range(_1d_intervals * _days)],  # not used
        employee_calendar=calendar,
        breaks=_12_h_breaks,
        break_delays=(min_break_delay, max_break_delay)
    )

    model.solve()
def test_1_month_400_employee():
    _days = 31
    _1h_interval = int(1 * 60 / 15)
    _9h_intervals = 9 * _1h_interval
    _1d_intervals = 24 * _1h_interval

    # employee shifts
    calendar = generate_12h_calendar(_days, 400)

    # Configuration of breaks
    # 1. Delays between breaks
    min_break_delay = int(1.5 * _1h_interval)
    max_break_delay = int(3.5 * _1h_interval)

    # 2. Break rules
    #    (min_start, max_start, duration)
    _12_h_breaks = get_12h_break_config()

    model = BreaksIntervalsScheduling(
        num_employees=len(calendar),
        num_intervals=_1d_intervals * _days,
        intervals_demand=[1 for _ in range(_1d_intervals * _days)],  # not used
        employee_calendar=calendar,
        breaks=_12_h_breaks,
        break_delays=(min_break_delay, max_break_delay)
    )

    model.solve()