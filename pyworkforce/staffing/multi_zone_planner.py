from pathlib import Path
import json
import pandas as pd
import numpy as np
from pyworkforce.utils.shift_spec import required_positions, get_shift_short_name, get_shift_coverage, unwrap_shift
from pyworkforce.plotters.scheduling import plot_xy_per_interval
import math
from datetime import datetime as dt
from pyworkforce.utils.common import get_datetime
from pyworkforce.scheduling import MinAbsDifference
from pyworkforce.rostering.binary_programming import MinHoursRoster
import random
import itertools

class MultiZonePlanner():
    def __init__(self,
        df: pd.DataFrame,
        meta: any,
        output_dir: str):

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
        self.df = df
        self.meta = meta
        self.timezones = list(map(lambda t: int(t['utc']), self.meta['employees']))
        self.ratio = 1.5 #For rostering

        group_by_schemas = [(k, list(g)[0]) for k, g in itertools.groupby(self.meta['employees'], lambda x: x['schemes'][0])]
        map_to_shifts = [ (self.get_shift_by_schema(i[0]), i[1]['utc'], i[1]['dup']) for i in group_by_schemas]
        self.shift_with_names = [ i + (self.get_shift_name_by_id(i[0]),)  for i in map_to_shifts]

        manpowers = np.array([i[2] for i in self.shift_with_names])
        manpowers_r = manpowers / manpowers.sum(axis = 0)
        for idx, i in enumerate(self.shift_with_names):
            self.shift_with_names[idx] +=  (manpowers_r[idx],)

    def solve(self):
        self.schedule()
        self.roster()
        self.roster_postprocess()

    def dump_stat_and_plot(self, shift_id, tzone, solution, df):
        resources_shifts = solution['resources_shifts']
        df3 = pd.DataFrame(resources_shifts)
        df3['shifted_resources_per_slot'] = df3.apply(lambda t: np.array(unwrap_shift(t['shift'])) * t['resources'], axis=1)
        df4 = df3[['day', 'shifted_resources_per_slot']].groupby('day', as_index=False)['shifted_resources_per_slot'].apply(lambda x: np.sum(np.vstack(x), axis = 0)).to_frame()
        np.set_printoptions(linewidth=np.inf, formatter=dict(float=lambda x: "%3.0i" % x))
        df4.to_csv(f'../shifted_resources_per_slot_{shift_id}.csv')
        arr = df4['shifted_resources_per_slot'].values
        arr = np.concatenate(arr)
        df['resources_shifts'] = arr.tolist()
        df.to_csv(f'../scheduling_output_stage2_{shift_id}.csv')

        plot_xy_per_interval(f'scheduling_{shift_id}.png', df, x='index', y=["positions", "resources_shifts"])

    def dump_scheduling_output_rostering_input(self, shift_id, tzone, days, num_resources, solution, shifts_spec):
        with open(f'../scheduling_output_{shift_id}.json', 'w') as f:
                f.write(json.dumps(solution, indent=2))

        resources_shifts = solution['resources_shifts']
        df1 = pd.DataFrame(resources_shifts)
        df2 = df1.pivot(index='shift', columns='day', values='resources').rename_axis(None, axis=0)

        df2['combined']= df2.values.tolist()

        rostering = {}
        rostering['num_days'] = days
        rostering['num_resources'] = num_resources
        rostering['shifts'] = list(shifts_spec.keys())
        rostering['min_working_hours'] = 176 # Dec 2022 #todo:
        rostering['max_resting'] = 9 # Dec 2022
        rostering['non_sequential_shifts'] = []
        rostering['required_resources'] = df2['combined'].to_dict()
        rostering['banned_shifts'] = []
        rostering['resources_preferences'] = []
        rostering['resources_prioritization'] = []

        with open(f'../scheduling_output_rostering_input_{shift_id}.json', 'w') as outfile:
            outfile.write(json.dumps(rostering, indent=2))

    def get_shift_by_schema(self, schema_guid):
        schema = next(t for t in self.meta['schemes'] if t['id'] == schema_guid)
        shiftId = schema['schemeShifts'][0]['shiftId']
        return shiftId

    def get_shift_name_by_id(self, id):
        shift = next(t for t in self.meta['shifts'] if t['id'] == id)
        shift_name = get_shift_short_name(shift)
        return shift_name

    def schedule(self):
        print("Start")
        print(self.shift_with_names)

        self.df['positions'] = self.df.apply(lambda row: required_positions(row['call_volume'], row['aht'], 15, row['art'], row['service_level']), axis=1)

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

        campaignUtc = int(self.meta['campaignUtc'])

        for party in self.shift_with_names:
            shift_id = party[0]
            shift_name = party[3]
            tzone = party[1]
            tzone_shift = int(tzone) - campaignUtc
            position_portion = party[4]
            position_requested = int(party[2])

            # shift = self.meta['shifts'][0] #todo map
            shift_names = [shift_name]
            shifts_spec = get_shift_coverage(shift_names, with_breaks=True)
            # cover_check = [int(any(l)) for l in zip(*shifts_spec.values())]

            df = self.df.copy()

            df['positions_quantile'] = df['positions'].apply(lambda t: math.ceil(t * position_portion))
            df = df.shift(periods=(-1 * ts * tzone_shift), fill_value = 0)
            df.to_csv(f'../scheduling_output_stage1_{shift_id}.csv')

            required_resources = []
            for i in range(days):
                df_short = df[i * DayH * ts : (i + 1) * DayH * ts]
                required_resources.append(df_short['positions_quantile'].tolist())

            scheduler = MinAbsDifference(num_days = days,  # S
                                periods = DayH * ts,  # P
                                shifts_coverage = shifts_spec,
                                required_resources = required_resources,
                                max_period_concurrency = int(df['positions_quantile'].max()),  # gamma
                                max_shift_concurrency=int(df['positions_quantile'].mean()),  # beta
                                )
            solution = scheduler.solve()

            self.dump_scheduling_output_rostering_input(
                shift_id,
                tzone,
                days,
                position_requested,
                solution,
                shifts_spec
            )

            self.dump_stat_and_plot(
                shift_id,
                tzone,
                solution,
                df.copy()
            )

        return "Done"


    def roster_postprocess(self):
        print("Start rostering postprocessing")

        for party in self.shift_with_names:
            shift_id = party[0]
            tzone = party[1]
            print(f'Shift: {shift_id}')

            with open(f'../scheduling_output_rostering_input_{shift_id}.json', 'r') as f:
                shifts_info = json.load(f)

            with open(f'../rostering_output_{shift_id}.json', 'r') as f:
                rostering = json.load(f)

            total_resources = rostering['total_resources']
            needed_resource = shifts_info["num_resources"]

            id_to_drop = random.sample(range(0, total_resources), total_resources - needed_resource)

            resource_shifts = rostering['resource_shifts']
            df = pd.DataFrame(resource_shifts)
            df = df[~df['id'].isin(id_to_drop)]
            
            rostering['total_resources'] = needed_resource
            rostering['resource_shifts'] = json.loads(df.to_json(orient='records'))

            with open(f'../rostering_output_final_{shift_id}.json', 'w') as f:
                f.write(json.dumps(rostering, indent = 2))

            df['shifted_resources_per_slot'] = df.apply(lambda t: np.array(unwrap_shift(t['shift'])) * 1, axis=1)
            df1 = df[['day', 'shifted_resources_per_slot']].groupby('day', as_index=False)['shifted_resources_per_slot'].apply(lambda x: np.sum(np.vstack(x), axis = 0)).to_frame()

            np.set_printoptions(linewidth=np.inf, formatter=dict(float=lambda x: "%3.0i" % x))
            arr = df1['shifted_resources_per_slot'].values
            arr = np.concatenate(arr)
            df3 = pd.read_csv(f'../scheduling_output_stage1_{shift_id}.csv')
            df3['resources_shifts'] = arr.tolist()

            plot_xy_per_interval(f'rostering_{shift_id}.png', df3, x='index', y=["positions", "resources_shifts"])

    def roster(self):
        print("Start rostering")
        for party in self.shift_with_names:
            shift_id = party[0]
            tzone = party[1]
            print(f'Shift: {shift_id}')
            with open(f'../scheduling_output_rostering_input_{shift_id}.json', 'r') as f:
                shifts_info = json.load(f)

            shift_names = shifts_info["shifts"]
            shifts_hours = [int(i.split('_')[1]) for i in shifts_info["shifts"]]
            print(shift_names)

            resources = [f'emp_{i}' for i in range(0, int(self.ratio * shifts_info["num_resources"]) )]

            solver = MinHoursRoster(num_days=shifts_info["num_days"],
                        resources=resources,
                        shifts=shifts_info["shifts"],
                        shifts_hours=shifts_hours,
                        min_working_hours=shifts_info["min_working_hours"],
                        max_resting=shifts_info["max_resting"],
                        non_sequential_shifts=shifts_info["non_sequential_shifts"],
                        banned_shifts=shifts_info["banned_shifts"],
                        required_resources=shifts_info["required_resources"],
                        resources_preferences=shifts_info["resources_preferences"],
                        resources_prioritization=shifts_info["resources_prioritization"])

            solution = solver.solve()

            with open(f'../rostering_output_{shift_id}.json', 'w') as f:
                f.write(json.dumps(solution, indent = 2))

        return "Done"