
def build_intervals_map(interval_minutes: int = 15, length_days: int = 1):

    _intervals_per_hour = 60/interval_minutes
    total_intervals = int(length_days*24*_intervals_per_hour)
    # todo: valiudate remainders

    intervals_map = {}
    times_map = {}

    for i in range(total_intervals):
        hours = int(i/_intervals_per_hour)
        minutes = int((float(i)/_intervals_per_hour - hours)*60)

        str = f"{hours:02}:{minutes:02}"
        intervals_map[str] = i
        times_map[i] = str

    return (intervals_map, times_map)


def build_break_spec(meta: dict, interval_minutes: int = 15):
    # input:
    # "activities": [
    #     {
    #         "id": "9 часов день обед",
    #         "duration": "00:30",
    #         "timeStart": "03:00",
    #         "timeEndStart": "05:30",
    #         "isPaid": false
    #     },
    #  ]
    #
    # output: (break_start_min, break_start_max, break_duration)

    (m, _) = build_intervals_map(interval_minutes)

    break_spec = []

    for a in meta["activities"]:
        id = a["id"]
        start = m[a["timeStart"]]
        start_end = m[a["timeEndStart"]]
        duration = m[a["duration"]]

        break_spec.append(
            (id, start, start_end, duration)
        )

    return break_spec


