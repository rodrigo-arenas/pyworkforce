from pyworkforce.utils.shift_spec import get_start_from_shift_short_name, get_duration_from_shift_short_name, \
    get_start_from_shift_short_name_mo


def test_get_start_from_shift_short_name_mo():

    start = get_start_from_shift_short_name_mo("3_9_6_15")
    assert start == "06:15"

    start = get_start_from_shift_short_name_mo("3_12_7_45")
    assert start == "07:45"


def test_get_duration_from_shift_short_name():

    duration = get_duration_from_shift_short_name("3_9_6_15")
    assert duration == 9

    duration = get_duration_from_shift_short_name("3_12_7_45")
    assert duration == 12

