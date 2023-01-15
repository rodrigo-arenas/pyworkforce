import datetime

import numpy as np
import pandas
from pyworkforce import ErlangC
from pyworkforce.utils.shift_spec import get_shift_coverage


def get_datetime(t):
    return datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')


def position_statistics(call_volume, aht, interval, art, service_level, positions):
    erlang = ErlangC(transactions=call_volume, aht=aht / 60.0, interval=interval, asa=art / 60.0, shrinkage=0.0)

    if (positions > 0):
        achieved_service_level = erlang.service_level(positions, scale_positions=False) * 100
        achieved_occupancy = erlang.achieved_occupancy(positions, scale_positions=False)
        waiting_probability = erlang.waiting_probability(positions=positions) * 100

        return (achieved_service_level, achieved_occupancy, waiting_probability)
    else:
        return (0, 0, 0)


def calculate_stats(shift_names, rostering_solution, df_csv: pandas.DataFrame):
    # todo: fix hardcoded Days number
    HMin = 60
    DayH = 24
    NDays = 31

    # 1. Get all possible shifts with daily coverage
    shifts_coverage = get_shift_coverage(shift_names)

    # 2. Get actual resources assignments per day & calculate the sum of resources
    # initiate daily zero sequences
    daily_demand = []
    for _ in range(NDays):
        # todo: fix hardcoded intervals
        daily_demand.append(np.zeros(96))

    # rostering data contains shoft assigment e.g. 0 0 0 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 per resource
    # => just sum everything to get overall day+intervals assignments
    for rs in rostering_solution['resource_shifts']:
        day = rs['day']  # day 1, day 2, ...
        shift = rs['shift']

        shift_array = np.array(shifts_coverage[shift])
        daily_demand[day - 1] += np.array(shift_array)

    # 3. Get input csv statistics & recalculate erlangs

    min_date = get_datetime(min(df_csv['tc']))
    max_date = get_datetime(max(df_csv['tc']))
    days = (max_date - min_date).days + 1
    date_diff = get_datetime(df_csv.iloc[1]['tc']) - get_datetime(df_csv.iloc[0]['tc'])
    step_min = int(date_diff.total_seconds() / HMin)

    ts = int(HMin / step_min)
    daily_intervals = DayH * ts

    for day in range(days):
        for i in range(daily_intervals):
            df_csv.loc[day * daily_intervals + i, "achieved_positions"] = daily_demand[day][i]

    df_csv['achieved_positions'] = df_csv['achieved_positions'].astype('int')

    for i in range(len(df_csv)):
        sl, occ, art = position_statistics(df_csv.loc[i, 'call_volume'], df_csv.loc[i, 'aht'], 15,
                                           df_csv.loc[i, 'art'], df_csv.loc[i, 'service_level'],
                                           df_csv.loc[i, 'achieved_positions'])
        df_csv.loc[i, 'achieved_sl'] = round(sl, 2)
        df_csv.loc[i, 'achieved_occ'] = round(occ, 2)
        df_csv.loc[i, 'achieved_art'] = round(art, 2)

    return df_csv
