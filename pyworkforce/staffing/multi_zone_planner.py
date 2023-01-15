from pathlib import Path
import json
import pandas as pd
import numpy as np

from pyworkforce.staffing.stats.calculate_stats import calculate_stats
from pyworkforce.utils.shift_spec import required_positions, get_shift_short_name, get_shift_coverage, unwrap_shift, \
    all_zeros_shift
from pyworkforce.plotters.scheduling import plot_xy_per_interval
import math
from datetime import datetime as dt
from pyworkforce.utils.common import get_datetime
from pyworkforce.scheduling import MinAbsDifference
from pyworkforce.rostering.binary_programming import MinHoursRoster
import random
import itertools
from strenum import StrEnum

class Statuses(StrEnum):
    NOT_STARTED = 'NOT_STARTED',
    UNKNOWN = 'UNKNOWN',
    MODEL_INVALID = 'MODEL_INVALID',
    FEASIBLE = 'FEASIBLE',
    INFEASIBLE = 'INFEASIBLE',
    OPTIMAL = 'OPTIMAL'

    def is_ok(self):
        return self in [Statuses.OPTIMAL, Statuses.FEASIBLE]

class MultiZonePlanner():
    def __init__(self,
        df: pd.DataFrame,
        meta: any,
        output_dir: str):

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
        self.df = df
        self.__df_stats = None
        self.meta = meta
        # self.timezones = list(map(lambda t: int(t['utc']), self.meta['employees']))

        # todo: replace this magic number with configured property or even better remove it
        self.rostering_ratio = 1.0  # For rostering

        # shift_with_name:
        #   (id, shift_name, utc, employees_count, , employee_ratio)
        self.shift_with_names = self.build_shifts()

        self.status = Statuses.NOT_STARTED

    def build_shifts(self):
        edf = pd.DataFrame(self.meta['employees'])
        edf['shiftId'] = edf.apply(lambda t: self.get_shift_by_schema(t['schemas'][0]), axis=1)
        edf_g = edf.groupby(['utc', 'shiftId'])['id'].agg(['count'])
        print(edf_g)

        shift_with_names = []

        # [('c8e4261e-3de3-4343-abda-dc65e4042494', '+6', 150, 'x_9_6_13_15', 0.410958904109589), ('c8e4261e-3de3-4343-abda-dc65e4042495', '+3', 33, 'x_9_6_13_15', 0.09041095890410959), ('c8e4261e-3de3-4343-abda-dc65e4042490', '+3', 32, 'x_12_6_13_15', 0.08767123287671233), ('22e4261e-3de3-4343-abda-dc65e4042496', '-3', 150, 'x_9_6_13_15', 0.410958904109589)]
        for index, row in edf_g.iterrows():
            utc = index[0]
            shift_orig_id = index[1]
            shift_name = self.get_shift_name_by_id(shift_orig_id, utc)
            employee_count = int(row['count'])  # by default its int64 -> non serializible

            shift_with_names.append(
                (shift_orig_id, shift_name, utc, employee_count, )
            )

        manpowers = np.array([i[2] for i in shift_with_names])  # i[2] == count
        manpowers_r = manpowers / manpowers.sum(axis=0)
        for idx, i in enumerate(shift_with_names):
            shift_with_names[idx] += (manpowers_r[idx],)

        return shift_with_names

    @property
    def df_stats(self):
        return self.__df_stats

    def solve(self):
        self.status = Statuses.NOT_STARTED

        # 1. Schedule shift
        self.schedule()
        if not self.status.is_ok():
            return self.status

        # 2. Assign resources per shifts
        self.roster()
        if not self.status.is_ok():
            return self.status

        # 3. Process results before return
        self.roster_postprocess()

        # 4. Recalculate statistics
        self.recalculate_stats()

        # return the latest status of the rostering model
        # should be either OPTIMAL or FEASIBLE
        return self.status

    def dump_stat_and_plot(self, shift_suffix, solution, df):
        resources_shifts = solution['resources_shifts']
        df3 = pd.DataFrame(resources_shifts)
        df3['shifted_resources_per_slot'] = df3.apply(lambda t: np.array(unwrap_shift(t['shift'])) * t['resources'], axis=1)
        df4 = df3[['day', 'shifted_resources_per_slot']].groupby('day', as_index=False)['shifted_resources_per_slot'].apply(lambda x: np.sum(np.vstack(x), axis = 0)).to_frame()
        np.set_printoptions(linewidth=np.inf, formatter=dict(float=lambda x: "%3.0i" % x))
        df4.to_csv(f'{self.output_dir}/shifted_resources_per_slot_{shift_suffix}.csv')
        arr = df4['shifted_resources_per_slot'].values
        arr = np.concatenate(arr)
        df['resources_shifts'] = arr.tolist()
        df.to_csv(f'{self.output_dir}/scheduling_output_stage2_{shift_suffix}.csv')

        plot_xy_per_interval(f'{self.output_dir}/scheduling_{shift_suffix}.png', df, x='index', y=["positions", "resources_shifts"])

    def dump_scheduling_output_rostering_input(self, shift_suffix, days, num_resources, solution, shifts_spec):
        with open(f'{self.output_dir}/scheduling_output_{shift_suffix}.json', 'w') as f:
                f.write(json.dumps(solution, indent=2))

        resources_shifts = solution['resources_shifts']
        df1 = pd.DataFrame(resources_shifts)
        df2 = df1.pivot(index='shift', columns='day', values='resources').rename_axis(None, axis=0)

        df2['combined']= df2.values.tolist()

        rostering = {
            'num_days': days,
            'num_resources': num_resources,
            'shifts': list(shifts_spec.keys()),
            'min_working_hours': 176,  # Dec 2022 #todo:
            'max_resting': 9,  # Dec 2022
            'non_sequential_shifts': [],
            'required_resources': df2['combined'].to_dict(),
            'banned_shifts': [],
            'resources_preferences': [],
            'resources_prioritization': []
        }

        with open(f'{self.output_dir}/scheduling_output_rostering_input_{shift_suffix}.json', 'w') as outfile:
            outfile.write(json.dumps(rostering, indent=2))

    def get_shift_by_schema(self, schema_id):
        schema = next(t for t in self.meta['schemas'] if t['id'] == schema_id)
        shift_id = schema['shifts'][0]['shiftId']
        return shift_id

    def get_shift_name_by_id(self, id, utc):
        shift = next(t for t in self.meta['shifts'] if t['id'] == id)
        shift_name = get_shift_short_name(shift, utc)
        return shift_name

    def schedule(self):
        print("Start")
        print(self.shift_with_names)

        self.df['positions'] = self.df.apply(lambda row: required_positions(
            call_volume=row['call_volume'],
            aht=row['aht'],
            interval=15*60, # interval should be passed within the same dimension as aht & art
            art=row['art'],
            service_level=row['service_level']
        ), axis=1)

        # Prepare required_resources
        HMin = 60
        DayH = 24
        min_date = min(self.df.index)
        max_date = max(self.df.index)
        days = (max_date - min_date).days + 1

        date_diff = self.df.index[1] - self.df.index[0]
        step_min = int(date_diff.total_seconds() / HMin)
        ts = int(HMin / step_min)

        self.df.index = self.df.index.tz_localize(tz='Europe/Moscow')

        campainUtc = int(self.meta['campainUtc'])

        for party in self.shift_with_names:
            (shift_id, shift_name, utc, positions_requested, position_portion) = party
            utc_shift = int(utc) - campainUtc

            # shift = self.meta['shifts'][0] #todo map
            shift_names = [shift_name]
            shifts_coverage = get_shift_coverage(shift_names, with_breaks=True)
            # cover_check = [int(any(l)) for l in zip(*shifts_spec.values())]

            df = self.df.copy()

            df['positions_quantile'] = df['positions'].apply(lambda t: math.ceil(t * position_portion))
            df = df.shift(periods=(-1 * ts * utc_shift), fill_value = 0)

            # shift_id -> shjft_name in prefix because id's will override each other from different zones
            df.to_csv(f'{self.output_dir}/scheduling_output_stage1_{shift_name}.csv')

            required_resources = []
            for i in range(days):
                df_short = df[i * DayH * ts : (i + 1) * DayH * ts]
                required_resources.append(df_short['positions_quantile'].tolist())

            scheduler = MinAbsDifference(num_days = days,  # S
                                periods = DayH * ts,  # P
                                shifts_coverage = shifts_coverage,
                                required_resources = required_resources,
                                max_period_concurrency = int(df['positions_quantile'].max()),  # gamma
                                max_shift_concurrency=int(df['positions_quantile'].mean()),  # beta
                                )

            solution = scheduler.solve()

            # if solution not feasible -> stop it and return result
            self.status = Statuses(solution['status'])
            if not self.status.is_ok():
                return

            self.dump_scheduling_output_rostering_input(
                shift_name,
                days,
                positions_requested,
                solution,
                shifts_coverage
            )

            self.dump_stat_and_plot(
                shift_name,
                solution,
                df.copy()
            )

        return "Done"

    def roster(self):
        print("Start rostering")
        for party in self.shift_with_names:
            (shift_id, shift_name, utc, *_) = party

            print(f'Shift: {shift_name}')
            with open(f'{self.output_dir}/scheduling_output_rostering_input_{shift_name}.json', 'r') as f:
                shifts_info = json.load(f)

            shift_names = shifts_info["shifts"]
            shifts_hours = [int(i.split('_')[1]) for i in shifts_info["shifts"]]
            print(shift_names)

            resources = [f'emp_{i}' for i in range(0, int(self.rostering_ratio * shifts_info["num_resources"]))]

            solver = MinHoursRoster(num_days=shifts_info["num_days"],
                                    resources=resources,
                                    shifts=shifts_info["shifts"],
                                    shifts_hours=shifts_hours,
                                    min_working_hours=shifts_info["min_working_hours"],
                                    max_resting=shifts_info["max_resting"],
                                    non_sequential_shifts=shifts_info["non_sequential_shifts"],
                                    banned_shifts=shifts_info["banned_shifts"],
                                    required_resources=shifts_info["required_resources"],
                                    max_search_time=5*60,
                                    strict_mode=False
                                    )

            solution = solver.solve()

            # if solution not feasible -> stop it and return result
            self.status = Statuses(solution['status'])
            if not self.status.is_ok():
                return

            with open(f'{self.output_dir}/rostering_output_{shift_name}.json', 'w') as f:
                f.write(json.dumps(solution, indent = 2))

        print("Done rostering")
        return "Done"

    def roster_postprocess(self):
        print("Start rostering postprocessing")

        # just a helper function to use
        def replace_nan(df, col, what):
            nans = df[col].isnull()
            df.loc[nans, col] = [what for isnan in nans.values if isnan]
            return df

        df_total = None

        for party in self.shift_with_names:
            (shift_id, shift_name, utc, *_) = party

            print(f'Shift: {shift_name} ({shift_id})')

            with open(f'{self.output_dir}/scheduling_output_rostering_input_{shift_name}.json', 'r') as f:
                shifts_info = json.load(f)

            with open(f'{self.output_dir}/rostering_output_{shift_name}.json', 'r') as f:
                rostering = json.load(f)

            df = pd.DataFrame(rostering['resource_shifts'])

            # this is virtual empty shift, to be used as a filler for rest days
            empty_shift = np.array(all_zeros_shift()) * 1
            empty_schedule = pd.DataFrame(index = [i for i in range(31)])   # todo: fix 31 day constant

            df['shifted_resources_per_slot'] = df.apply(
                lambda t: np.array(unwrap_shift(t['shift'])) * 1, axis=1
            )

            df1 = df[['day', 'shifted_resources_per_slot']].groupby('day', as_index=True)[
                'shifted_resources_per_slot'].apply(lambda x: np.sum(np.vstack(x), axis=0)).to_frame()

            # on missed indexes (=days), nan will be placed, because there are no any rest days in df1
            df1 = pd.concat([df1, empty_schedule], axis=1)
            df1 = replace_nan(df1, 'shifted_resources_per_slot', empty_shift)
            # new items are at the end with propper index - just sort them to be moved to correct position
            df1 = df1.sort_index(ascending=True)

            np.set_printoptions(linewidth=np.inf, formatter=dict(float=lambda x: "%3.0i" % x))
            arr = df1['shifted_resources_per_slot'].values
            arr = np.concatenate(arr)
            df3 = pd.read_csv(f'{self.output_dir}/scheduling_output_stage1_{shift_name}.csv')
            df3['resources_shifts'] = arr.tolist()

            plot_xy_per_interval(f'{self.output_dir}/rostering_{shift_name}.png', df3, x='index', y=["positions", "resources_shifts"])

            if df_total is None:
                df_total = df3
            else:
                df_total['resources_shifts'] += df3['resources_shifts']

        plot_xy_per_interval(f'{self.output_dir}/rostering.png', df_total, x='index', y=["positions", "resources_shifts"])

        print("Done rostering postprocessing")
        return "Done"



    def recalculate_stats(self):
        # TODO:
        if False:
            self.__df_stats = calculate_stats(None, None, None)

