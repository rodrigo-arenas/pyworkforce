import json
import os

from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

from pprint import PrettyPrinter
from pyworkforce.utils.shift_spec import get_shift_coverage
from pyworkforce.plotters.matplotlib import plot

scheduler_data_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(scheduler_data_path, '../rostering_output.json'), 'r') as f:
    solution = json.load(f)

pp = PrettyPrinter(indent=2)

shifts = ["Day_9_6_13_15", "Night_9_21_22_15"]
shifts_spec = get_shift_coverage(shifts)

shift_colors = {}
for i in shifts_spec.keys():
  if "Day" in i:
    shift_colors[i] = '#34eb46'
  else:
    shift_colors[i] = '#0800ff'

plot(solution, shifts_spec, 15, 31, shift_colors, "../Dec2022_562_employees.png", fig_size=(15,8))
