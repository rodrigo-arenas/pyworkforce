import datetime

import numpy as np
import pandas
from pyworkforce import ErlangC
from pyworkforce.utils.shift_spec import get_shift_coverage


def get_datetime(t):
    return datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')


def positions_service_level(call_volume, aht, interval, art, positions):
    erlang = ErlangC(transactions=call_volume, aht=aht, interval=interval, asa=art, shrinkage=0.0)

    if positions <= 0:
        return (0.0, 0.0)

    asa = erlang.what_asa(positions)
    if asa <=0:
        return (0.0, asa)

    service_level = erlang.service_level(positions, scale_positions=False, asa=asa) * 100

    # (service_level, asa)
    return (service_level, asa)


def calculate_stats(df: pandas.DataFrame):

    # ['tc', 'call_volume', 'service_level', 'art', 'positions', 'scheduled_positions']

    for i in range(len(df)):
        (sl, asa) = positions_service_level(
            call_volume=df.loc[i, 'call_volume'],
            aht = df.loc[i, 'aht'],
            interval=15*60,
            art=df.loc[i, 'art'],
            positions=df.loc[i, 'scheduled_positions'])

        df.loc[i, 'scheduled_service_level'] = round(sl, 2)
        df.loc[i, 'scheduled_asa'] = round(asa, 2)

    return df
