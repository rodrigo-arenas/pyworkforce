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
import numpy as np
from collections import deque

from pyworkforce.plotters.scheduling import plot, plot_xy_per_interval
from pyworkforce.utils.shift_spec import get_shift_coverage, get_shift_colors, decode_shift_spec, unwrap_shift
from pyworkforce.utils.common import get_datetime
from pyworkforce.staffing import MultiZonePlanner
import pytz
eastern = pytz.timezone('US/Eastern')


input_csv_path = '../scheduling_input.csv'
input_meta_path = '../scheduling_meta_input.json'
output_dir = '..'

Path(output_dir).mkdir(parents=True, exist_ok=True)
df = pd.read_csv(input_csv_path, parse_dates=[0], index_col=0)

with open(input_meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

mzp = MultiZonePlanner(df, meta, output_dir)
# mzp.solve()

mzp.schedule()
# mzp.roster()
# mzp.roster_postprocess()
