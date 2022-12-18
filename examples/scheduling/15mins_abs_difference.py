"""
Requirement: Find the number of workers needed to schedule per shift in a production plant for the next 2 days with the
    following conditions:
    * There is a number of required persons per hour and day given in the matrix "required_resources"
    * There are 4 available scheduling called "Morning", "Afternoon", "Night", "Mixed"; their start and end hour is
      determined in the dictionary "shifts_coverage", 1 meaning the shift is active at that hour, 0 otherwise
    * The number of required workers per day and period (hour) is determined in the matrix "required_resources"
    * The maximum number of workers that can be shifted simultaneously at any hour is 25, due plat capacity restrictions
    * The maximum number of workers that can be shifted in a same shift, is 20
"""
from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

from pyworkforce.scheduling import MinAbsDifference
from pyworkforce.queuing import ErlangC
from pprint import PrettyPrinter
import pandas as pd
import math
import json
from collections import deque

from pyworkforce.plotters.scheduling import plot
from pyworkforce.utils.shift_spec import get_shift_coverage, get_shift_colors, decode_shift_spec

def upscale_and_shift(a, time_scale, shift_right_pos):
  scaled = [val for val in a for _ in range(time_scale)]
  items = deque(scaled)
  items.rotate(shift_right_pos)
  return list(items)

def genereate_shifts_coverage(shift_hours, name, horizon_in_hours, start_hour, end_hour, step_mins):
  time_scale = int(60 / step_mins)
  slots = time_scale * (end_hour - start_hour)
  res = {}
  for i in range(slots):
    s_name = f'{name}_{horizon_in_hours}_{start_hour + (i * step_mins // 60)}_{i * step_mins % 60}'
    res[s_name] = upscale_and_shift(shift_hours, time_scale, i)
  return res

df = pd.read_csv('../scheduling_input.csv')

def required_positions(call_volume, aht, interval, art, service_level):
  erlang = ErlangC(transactions=call_volume, aht=aht / 60.0, interval=interval, asa=art / 100.0, shrinkage=0.0)
  positions_requirements = erlang.required_positions(service_level=service_level / 100.0, max_occupancy=1.00)
  return positions_requirements['positions']

df['positions'] = df.apply(lambda row: required_positions(row['call_volume'], row['aht'], 15, row['art'], row['service_level']), axis=1)

from datetime import datetime
def get_datetime(t):
  return datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')

min_date = get_datetime(min(df['tc']))
max_date = get_datetime(max(df['tc']))
days = (max_date - min_date).days + 1
date_diff = get_datetime(df.iloc[1]['tc']) - get_datetime(df.iloc[0]['tc'])
step_min = int(date_diff.total_seconds() / 60)
HMin = 60
DayH = 24
ts = int(HMin / step_min)
required_resources = []
for i in range(days):
  df0 = df[i * DayH * ts : (i + 1) * DayH * ts]
  required_resources.append(df0['positions'].tolist())

max_rr = int(df['positions'].max())
max_rr_norm = math.ceil(max_rr / DayH * ts)

shifts = ["Day_9_6_13_15", "Night_9_21_22_15"]
shifts_spec = get_shift_coverage(shifts)

cover_check = [int(any(l)) for l in zip(*shifts_spec.values())]
print(cover_check)

scheduler = MinAbsDifference(num_days = days,  # S
                                 periods = 24 * ts,  # P
                                 shifts_coverage = shifts_spec,
                                 required_resources = required_resources,
                                 max_period_concurrency = int(df['positions'].max()),  # gamma
                                 max_shift_concurrency=int(df['positions'].mean()),  # beta
                                 )

solution = scheduler.solve()
pp = PrettyPrinter(indent=2)
pp.pprint(solution)

shift_names = list(shifts_spec.keys())
shift_colors = get_shift_colors(shift_names)

# try:
#     plot(solution, 
#     shifts_spec, 
#     step_min, 
#     days, 
#     shift_colors, 
#     # f'image.png', 
#     fig_size=(12,5))
# except ArithmeticError:
#     print("plot error")

resources_shifts = solution['resources_shifts']

df1 = pd.DataFrame(resources_shifts)
df2 = df1.pivot(index='shift', columns='day', values='resources').rename_axis(None, axis=0)

df2['combined']= df2.values.tolist()

rostering = {}
rostering['num_days'] = days
rostering['num_resources'] = 375
rostering['shifts'] = list(shifts_spec.keys())
rostering['min_working_hours'] = 176 # Dec 2022
rostering['max_resting'] = 9 # Dec 2022
rostering['non_sequential_shifts'] = []
rostering['required_resources'] = df2['combined'].to_dict()
rostering['banned_shifts'] = []
rostering['resources_preferences'] = []
rostering['resources_prioritization'] = []

with open('../scheduling_output_rostering_input.json', 'w') as outfile:
    outfile.write(json.dumps(rostering, indent=2))