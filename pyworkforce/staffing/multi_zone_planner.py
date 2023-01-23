import codecs
from pathlib import Path
import json

import pandas as pd
import numpy as np

from pyworkforce.breaks.breaks_intervals_scheduling_sat import BreaksIntervalsScheduling
from pyworkforce.staffing.stats.calculate_stats import calculate_stats
from pyworkforce.utils.breaks_spec import build_break_spec, build_intervals_map
from pyworkforce.utils.shift_spec import get_start_from_shift_short_name, get_start_from_shift_short_name_mo, \
    required_positions, get_shift_short_name, get_shift_coverage, unwrap_shift, \
    all_zeros_shift, get_duration_from_shift_short_name
from pyworkforce.plotters.scheduling import plot_xy_per_interval
import math
from datetime import datetime as dt
from datetime import datetime, timedelta
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

        # id -> (id, start_interval, endstart_interval, duration_interval)
        self.activities_by_id = self.build_activities_specs()

        self.shift_activities = self.build_shift_with_activities()

        self.status = Statuses.NOT_STARTED

    def build_shifts(self):
        edf = pd.DataFrame(self.meta['employees'])
        edf['schema'] = edf.apply(lambda t: t['schemas'][0], axis=1)
        edf['shiftId'] = edf.apply(lambda t: self.get_shift_by_schema(t['schema']), axis=1)
        edf_g = edf.groupby(['utc', 'shiftId', 'schema'])['id'].agg(['count'])
        shift_with_names = []

        # [('c8e4261e-3de3-4343-abda-dc65e4042494', '+6', 150, 'x_9_6_13_15', 0.410958904109589), ('c8e4261e-3de3-4343-abda-dc65e4042495', '+3', 33, 'x_9_6_13_15', 0.09041095890410959), ('c8e4261e-3de3-4343-abda-dc65e4042490', '+3', 32, 'x_12_6_13_15', 0.08767123287671233), ('22e4261e-3de3-4343-abda-dc65e4042496', '-3', 150, 'x_9_6_13_15', 0.410958904109589)]
        for index, row in edf_g.iterrows():
            utc = index[0]
            shift_orig_id = index[1]
            schema_name = index[2]
            shift_name = self.get_shift_name_by_id(shift_orig_id, utc)
            employee_count = int(row['count'])  # by default its int64 -> non serializible

            shift_with_names.append(
                (shift_orig_id, shift_name, utc, employee_count, schema_name,)
            )

        manpowers = np.array([i[3] for i in shift_with_names])  # i[2] == count
        manpowers_r = manpowers / manpowers.sum(axis=0)
        for idx, i in enumerate(shift_with_names):
            shift_with_names[idx] += (manpowers_r[idx],)

        return shift_with_names

    def build_activities_specs(self):
        activities_specs = build_break_spec(self.meta)
        #   "9 часов день обед" -> ("9 часов день обед", "02:00", "07:00", "00:15")
        activities_map = {**{b: (b, *_) for (b, *_) in activities_specs}}

        return activities_map

    def build_shift_with_activities(self):
        (m, _) = build_intervals_map()
        shifts = {}

        for s in self.meta["shifts"]:
            s_id = s["id"]
            activities = s["activities"]
            min_between = m[s["minIntervalBetweenActivities"]]
            max_between = m[s["maxIntervalBetweenActivities"]]

            # (activities_id[], min_interval_between, max_interval_between)
            shifts[s_id] = (activities, min_between, max_between)

        return shifts

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

        # 3. Roster breaks
        self.roster_breaks()

        # 4. Process results before return
        self.roster_postprocess()

        # 5. Combine all in one json
        self.combine_results()

        # 6. Recalculate statistics
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

    def get_breaks_intervals_per_slot(self, resource_break_intervals: dict):
        # "resource" ->  [(day_num, break_id, start, end)]
        _days = 31
        _interval_per_hour = 4
        empty_month = np.zeros(_days * 24 * _interval_per_hour).astype(int)
        _eom = len(empty_month)

        # output: [ (resource(string), day, [010101010101]) ]
        result = []

        for resource_id, bi in resource_break_intervals.items():
            resource_month = empty_month.copy()
            for (day_num, break_id, start, end) in bi:
                # breaks are calculated with overnights also
                # => for the last day of month it could plan for a day after that.
                if start > _eom:
                    continue
                resource_month[start:end] = [1 for _ in range(start, min(end, _eom))]

            for d in range(_days):
                day_start = d * 24 * _interval_per_hour
                day_end_exclusive = (d + 1) * 24 * _interval_per_hour
                result.append(
                    (str(resource_id), int(d), resource_month[day_start:day_end_exclusive])
                )

        return result

    def get_breaks_per_day(self, resource_break_intervals: dict):
        # "resource" ->  [(day_num, break_id, start, end)]
        _days = 31
        _interval_per_hour = 4
        _full_day = 24*_interval_per_hour
        _eom = _days * _full_day

        (_, t) = build_intervals_map()

        # output: [ (resource, day, break_id, start_time, end_time ]
        result = []

        for resource_id, bi in resource_break_intervals.items():
            for (day_num, break_id, start, end) in bi:
                # breaks are calculated with overnights also
                # => for the last day of month it could plan for a day after that.
                if start > _eom:
                    continue

                # day_n = int(start/_full_day)
                day_n = day_num

                start_from_day = start - day_n*_full_day
                # for overnight intervals -> return next day's time
                if (start_from_day >= _full_day):
                    start_from_day -= _full_day

                end_from_day_inclusive = end - day_n*_full_day
                #end_from_day_inclusive = (end - 1) - day_n * _full_day
                if (end_from_day_inclusive >= _full_day):
                    end_from_day_inclusive -= _full_day

                start_time = t[start_from_day]
                end_time = t[end_from_day_inclusive]

                result.append(
                    (str(resource_id), day_n, break_id, start_time, end_time)
                )

        return result

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
            (shift_id, shift_name, utc, positions_requested, schema, position_portion) = party
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

            # todo: fix later
            if shifts_hours[0] == 12:
                # 12h shifts -> 10.5 * 16 = 176
                max_shifts_count = 16
            elif shifts_hours[0] == 9:
                # 9h shifts -> 8 * 22 = 176
                max_shifts_count = 22
            else:
                max_shifts_count = 0


            edf = pd.DataFrame(self.meta['employees'])
            edf['shiftId'] = edf.apply(lambda t: self.get_shift_by_schema(t['schemas'][0]), axis=1)
            edf_filtered = edf[(edf['utc'] == utc) & (edf['shiftId'] == shift_id)]
            # print(list(tt['id']))

            # resources = [f'emp_{i}' for i in range(0, int(self.rostering_ratio * shifts_info["num_resources"]))]

            resources = list(edf_filtered['id'])
            print(f'Rostering num: {shifts_info["num_resources"]} {len(resources)}')

            # constraint:
            #   (hard_min, soft_min, penalty, soft_max, hard_max, penalty)
            constraints = [
                # minimum 4 day of work, but no more than 6 days of work - theses are hard constraints
                # 5 -- is an optimal value, it penalize 1 in case of difference from 5
                # (4, 5, 1, 5, 6, 0),

                # no low bound, optimum - from 5 to 5 without penalty, more than 5 are forbidden
                (0, 5, 0, 5, 5, 0)
            ]

            solver = MinHoursRoster(num_days=shifts_info["num_days"],
                                    resources=resources,
                                    shifts=shifts_info["shifts"],
                                    #shifts_hours=shifts_hours,
                                    shifts_hours=0,
                                    min_working_hours=shifts_info["min_working_hours"],
                                    max_shifts_count = max_shifts_count,
                                    # max_resting=shifts_info["max_resting"],
                                    # we don't have constraints on max resting time
                                    max_resting=0,
                                    non_sequential_shifts=shifts_info["non_sequential_shifts"],
                                    banned_shifts=shifts_info["banned_shifts"],
                                    required_resources=shifts_info["required_resources"],
                                    max_search_time=5*60,
                                    strict_mode=False,
                                    shift_constraints=constraints
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


    def roster_breaks(self):
        print("Start breaks rostering")
        (m, _) = build_intervals_map()

        def daily_start_index(day):
            return day*24*4

        def get_working_intervals(edf: pd.DataFrame):
            edf["day_index"] = edf.apply(lambda row: daily_start_index(row["day"]), axis=1)
            edf["start_interval"] = \
                edf["day_index"] + edf.apply(lambda row: m[get_start_from_shift_short_name_mo(row["shift"])], axis=1)
            edf["duration_interval"] = edf.apply(lambda row: get_duration_from_shift_short_name(row["shift"]), axis=1) * 4  # durations are in hours
            edf["end_interval"] = edf["start_interval"] + edf["duration_interval"]

            return edf[["day", "start_interval", "end_interval"]].to_records(index=False).tolist()

        # 0. iterate over known shifts, breaks are same for employees within given shift
        for party in self.shift_with_names:
            (shift_id, shift_name, utc, *_) = party

            print(f'Shift: {shift_name} ({shift_id})')

            # 1. Summarize breaks details
            (breaks_ids, min_delay, max_delay) = self.shift_activities[shift_id]
            breaks_specs = [self.activities_by_id[b] for b in breaks_ids]

            # 2. Rostering gives Employee' schedules
            with open(f'{self.output_dir}/rostering_output_{shift_name}.json', 'r') as f:
                rostering = json.load(f)

            df = pd.DataFrame(rostering['resource_shifts'])
            employee_schedule = {}
            for (index, df_e) in df.groupby(["resource"]):
                employee_schedule[index] = get_working_intervals(df_e)

            # 3. Run model
            model = BreaksIntervalsScheduling(
                employee_calendar=employee_schedule,
                breaks=breaks_specs,
                break_min_delay=min_delay,
                break_max_delay=max_delay
            )

            solution = model.solve()

            with codecs.open(f'{self.output_dir}/breaks_output_{shift_name}.json', 'w', encoding='utf-8') as f:
                json.dump(solution, f, indent=2, ensure_ascii=False)


        print("Done breaks rostering")
        return "Done"


    def roster_postprocess(self):
        print("Start rostering postprocessing")

        # just a helper function to use
        def replace_nan(df, col, what):
            nans = df[col].isnull()
            df.loc[nans, col] = [what for isnan in nans.values if isnan]
            return df

        def to_df_stats(df: pd.DataFrame):
            interested_columns = ['tc', 'call_volume', 'aht', 'service_level', 'art', 'positions', 'resources_shifts']

            df = df[interested_columns]
            df = df.rename(columns={'resources_shifts': 'scheduled_positions'})

            return df

        df_total = None

        for party in self.shift_with_names:
            (shift_id, shift_name, utc, *_) = party

            print(f'Shift: {shift_name} ({shift_id})')

            # Load breaks and converto to df
            with open(f'{self.output_dir}/breaks_output_{shift_name}.json', 'r', encoding='utf-8') as f:
                breaks = json.load(f)
            list_breaks = self.get_breaks_intervals_per_slot(breaks['resource_break_intervals'])
            df_breaks = pd.DataFrame(list_breaks, columns=["resource", "day", "breaks"])
            df_breaks.set_index(["resource", "day"], inplace=True)

            # Load rostering data
            with open(f'{self.output_dir}/rostering_output_{shift_name}.json', 'r') as f:
                rostering = json.load(f)
            df = pd.DataFrame(rostering['resource_shifts'])

            # This is virtual empty shift, to be used as a filler for rest days
            empty_shift = np.array(all_zeros_shift()) * 1
            empty_schedule = pd.DataFrame(index = [i for i in range(31)])   # todo: fix 31 day constant

            # Rostering - breaks = schedule
            df['shifted_resources_per_slot'] = df.apply(
                lambda t: np.array(unwrap_shift(t['shift'])) * 1 - df_breaks.loc[str(t['resource']), t['day']][0], axis=1
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

        print(df_total)
        plot_xy_per_interval(f'{self.output_dir}/rostering.png', df_total, x='index', y=["positions", "resources_shifts"])

        self.__df_stats = to_df_stats(df_total)

        print("Done rostering postprocessing")
        return "Done"

    def combine_results(self):
        campain_utc = self.meta['campainUtc']
        out = {
            "campainUtc": campain_utc,
            "campainSchedule": []
        }
        campainSchedule = out['campainSchedule']
        for party in self.shift_with_names:
            (shift_name, shift_code, utc, mp, schema_name, q) = party

            print(f'Shift: {shift_name} ({shift_name})')

            # Load breaks and converto to df
            with open(f'{self.output_dir}/breaks_output_{shift_code}.json', 'r', encoding='utf-8') as f:
                breaks = json.load(f)
            list_breaks = self.get_breaks_per_day(breaks['resource_break_intervals'])
            # output: [ (resource, day, break_id, start_time, end_time ]
            df_breaks = pd.DataFrame(list_breaks, columns=["resource", "day", "activityId", "activityTimeStart", "activityTimeEnd"])
            df_breaks.set_index(["resource", "day"], inplace=True)

            with open(f'{self.output_dir}/rostering_output_{shift_code}.json', 'r') as f:
                rostering = json.load(f)

            df = pd.DataFrame(rostering['resource_shifts'])
            df['shiftTimeStartLocal'] = df.apply(
                lambda t: get_start_from_shift_short_name(t['shift']), axis=1
            )

            delta = utc - campain_utc

            df['schemaId'] = schema_name
            df['shiftId'] = shift_name
            df['employeeId'] = df['resource']
            df['employeeUtc'] = utc
            min_date = min(self.df.index)

            df['shiftTimeStart'] = df.apply(
                lambda t: format(dt.strptime(t['shiftTimeStartLocal'], "%H:%M:%S") + timedelta(hours=delta), '%H:%M'),
                axis=1)
            df['shiftDate'] = df.apply(lambda t: format(min_date + timedelta(hours=delta) + timedelta(days=t['day']), "%d.%m.%y"), axis=1)

            df_breaks['activityTimeStart'] = df_breaks.apply(
                lambda t: format(dt.strptime(t['activityTimeStart'], "%H:%M") + timedelta(hours=delta), '%H:%M'),
                axis=1)

            df_breaks['activityTimeEnd'] = df_breaks.apply(
                lambda t: format(dt.strptime(t['activityTimeEnd'], "%H:%M") + timedelta(hours=delta), '%H:%M'),
                axis=1)

            df['activities'] = df.apply(
                lambda t: df_breaks.loc[str(t['employeeId']), t['day']],
                axis=1
            )

            res = json.loads(df[['employeeId', 'employeeUtc', 'schemaId', 'shiftId', 'shiftDate', 'shiftTimeStart',
                                 'activities']].to_json(orient="records"))
            campainSchedule.extend(res)

        with open(f'{self.output_dir}/rostering.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(out, indent=2, ensure_ascii=False))

    def recalculate_stats(self):
        if self.__df_stats is None:
            return

        print("Recalculate statistics: start")

        self.__df_stats = calculate_stats(self.__df_stats)

        # dump statistics to .json
        result = self.__df_stats.to_json(orient="records")
        parsed = json.loads(result)

        print("Writing statistics to .json")

        with open(f'{self.output_dir}/statistics_output.json', 'w') as f:
            f.write(json.dumps(parsed, indent=2))

        print("Recalculate statistics: done")

