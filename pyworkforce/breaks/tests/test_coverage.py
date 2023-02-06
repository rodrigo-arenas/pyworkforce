from random import randrange

from numpy.testing import assert_array_equal

from pyworkforce.breaks.breaks_coverage import calculate_coverage

_1h = int(1 * 60 / 15)
_12h = 12 * _1h
_1D = 24 * _1h

def generate_12h_calendar(num_days, num_workers):
    schedule = {}

    for w in range(num_workers):
        _start = randrange(6*_1h, 12*_1h)
        schedule[w] = [ (d, d * _1D + _start, d * _1D + _start + 12 * _1h) for d in range(num_days)]

    return schedule

def test_calculate_coverage_1worker_1day():
    schedule = {}

    for w in range(1):
        _start = randrange(6 * _1h, 12 * _1h)
        schedule[w] = [(d, d * _1D + _start, d * _1D + _start + 12 * _1h) for d in
                       range(1)]

    coverage = calculate_coverage(schedule, _1D)

    assert len(coverage) == 24*4

def test_calculate_coverage_2workers_3days():

    expected = []

    #           1h = 4 intervals (by 15 minutes), 1d = 24h
    #           d1                      |d2                      |d3
    #           hhhhhhhhhhhhhhhhhhhhhhhh|hhhhhhhhhhhhhhhhhhhhhhhh|hhhhhhhhhhhhhhhhhhhhhhhh
    # worker 1: xxxxxxxxx               |    xxxxxxxxx         xx|xxxxxxx
    # worker 2:         xxxxxxxxx       |               xxxxxxxxx|               xxxxxxxxx
    #           ------------------------|------------------------|------------------------
    #           111111112111111110000000|000011111111100111111122|111111100000000111111111

    # day 1
    expected.extend([1 for _ in range(8 * 4)])
    expected.extend([2 for _ in range(1 * 4)])
    expected.extend([1 for _ in range(8 * 4)])
    expected.extend([0 for _ in range(7 * 4)])

    # day 2
    expected.extend([0 for _ in range(4 * 4)])
    expected.extend([1 for _ in range(9 * 4)])
    expected.extend([0 for _ in range(2 * 4)])
    expected.extend([1 for _ in range(7 * 4)])
    expected.extend([2 for _ in range(2 * 4)])

    # day 3
    expected.extend([1 for _ in range(7 * 4)])
    expected.extend([0 for _ in range(8 * 4)])
    expected.extend([1 for _ in range(9 * 4)])


    schedule = {
        'worker 1': [
            (0, 0, 9*_1h),
            (1, _1D + 4*_1h, _1D + 13*_1h),
            (1, _1D + 22 * _1h, 2 * _1D + 7 * _1h),
        ],
        'worker 2': [
            (0, 8*_1h, 17 * _1h),
            (1, _1D + 15*_1h, _1D + 24*_1h),
            (2, 2*_1D + 15*_1h, 2*_1D + 24*_1h),
        ]
    }

    coverage = calculate_coverage(schedule, 3*_1D)

    assert len(coverage) == 3*24*4
    assert len(coverage) == len(expected)

    assert_array_equal(expected, coverage)