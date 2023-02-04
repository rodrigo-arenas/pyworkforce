from random import randrange
from pyworkforce.breaks.breaks_intervals_scheduling_sat import BreaksIntervalsScheduling, AdjustmentMode
from pyworkforce.breaks.breaks_printer import BreaksPrinter


_days = 7
_1h_interval = int(1 * 60 / 15)
_1d_intervals = 24 * _1h_interval
_30m = 2

# employee shifts
schedule = {}
# workers
for w in range(20):
    schedule[w] = [(d, d * _1d_intervals + 9 * _1h_interval, d * _1d_intervals + 18 * _1h_interval) for d in range(_days)]

# Configuration of breaks
# 1. Delays between breaks
min_break_delay = int(1.5 * _1h_interval)
max_break_delay = int(3.5 * _1h_interval)

# 2. Break rules
# (id, start)_index, end_index)
_12_h_breaks = [
    # lunch break: 02:00 -> 06:00, 30min
    ('lunch', 2 * _1h_interval, 6 * _1h_interval, 2),

    # just break: 01:30 -> 07:00, 15min
    ('break1', 1 * _1h_interval + _30m, 7 * _1h_interval, 1),

    # just break: 01:30 -> 07:00, 15min
    ('break2', 1 * _1h_interval + _30m, 7 * _1h_interval, 1),
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
    break_max_delay=int(3.5 * _1h_interval),
    make_adjustments=AdjustmentMode.ByExpectedAverage,
    num_days=_days
)

solution = model.solve()

printer = BreaksPrinter(num_intervals=_1d_intervals * _days,
                        intervals_per_hour=4,
                        employee_calendar=schedule,
                        solution=solution,
                        break_symbols=pictures)

printer.print()
