from random import randrange
from pyworkforce.breaks.breaks_intervals_scheduling_sat import BreaksIntervalsScheduling
from pyworkforce.breaks.breaks_printer import BreaksPrinter


_days = 7
_1h_interval = int(1 * 60 / 15)
_1d_intervals = 24 * _1h_interval
_30m = 2

# employee shifts
schedule = {}
# workers
for w in range(20):
    _start = randrange(6 * _1h_interval, 12 * _1h_interval)
    schedule[w] = [(d, d * _1d_intervals + _start, d * _1d_intervals + _start + 12 * _1h_interval) for d in range(_days)]

# Configuration of breaks
# 1. Delays between breaks
min_break_delay = int(1.5 * _1h_interval)
max_break_delay = int(3.5 * _1h_interval)

# 2. Break rules
# (id, start)_index, end_index)
_12_h_breaks = [
    # lunch break: 03:00 -> 08:0, 30min
    ('lunch', 3 * _1h_interval, 8 * _1h_interval, 2),

    # just break: 05:30 -> 11:00, 15min
    ('break1', 5 * _1h_interval + _30m, 11 * _1h_interval, 1),

    # just break: 01:00 -> 10:30, 15min
    ('break2', 1 * _1h_interval, 10 * _1h_interval + _30m, 1),
]

pictures = {
    "lunch": u'□',
    "break1": u'♪',
    "break2": u'♠',
}

model = BreaksIntervalsScheduling(
    num_employees=len(schedule),
    num_intervals=_1d_intervals * _days,
    # intervals_demand=[1 for _ in range(_1d_intervals * _days)],  # not used
    employee_calendar=schedule,
    breaks=_12_h_breaks,
    break_min_delay=int(1.5 * _1h_interval),
    break_max_delay=int(3.5 * _1h_interval)
)

solution = model.solve()

printer = BreaksPrinter(num_intervals=_1d_intervals * _days,
                        intervals_per_hour=4,
                        employee_calendar=schedule,
                        solution=solution,
                        break_symbols=pictures)

printer.print()
