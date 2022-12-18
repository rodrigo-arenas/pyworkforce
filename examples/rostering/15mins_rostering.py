import json
import os

from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

from pyworkforce.rostering.binary_programming import MinHoursRoster
from pprint import PrettyPrinter
# from pyworkforce.utils.shift_spec import get_shift_coverage, get_shift_colors, decode_shift_spec

# from pyworkforce import plotters

scheduler_data_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(scheduler_data_path, '../scheduling_output_rostering_input.json'), 'r') as f:
    shifts_info = json.load(f)

pp = PrettyPrinter(indent=2)
pp.pprint(shifts_info)

resources = [f'emp_{i}' for i in range(0, int(1.5 * shifts_info["num_resources"]) )]

shift_names = shifts_info["shifts"]
shifts_hours = [int(i.split('_')[1]) for i in shifts_info["shifts"]]

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
pp.pprint(solution)

with open('../rostering_output.json', 'w') as outfile:
    outfile.write(json.dumps(solution, indent=2))
