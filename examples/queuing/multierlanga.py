"""
Evaluate many Erlang A scenarios at once and view them as a DataFrame.

Sweeps the customer patience parameter to see how impatience affects the
required staffing and the abandonment probability.
"""

from pyworkforce.queuing import MultiErlangA
from pyworkforce.utils import results_to_dataframe

param_grid = {
    "transactions": [100],
    "aht": [3],
    "interval": [30],
    "asa": [20 / 60],
    "patience": [3, 5, 10],
    "shrinkage": [0.3],
}

multi = MultiErlangA(param_grid=param_grid, n_jobs=-1)

results = multi.required_positions({
    "service_level": [0.8],
    "max_occupancy": [0.85],
    "max_abandonment": [0.05],
})

df = results_to_dataframe(results, multi.required_positions_params)
columns = ["patience", "raw_positions", "positions",
           "service_level_result", "abandonment_probability"]
print(df[columns].round(4).to_string(index=False))
