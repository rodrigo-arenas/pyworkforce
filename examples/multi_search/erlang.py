from pyworkforce.multi_search import MultiErlangC

param_grid = {"transactions": [100, 200], "aht": [3], "interval": [30], "asa": [20 / 60], "shrinkage": [0.3]}
required_positions_arguments = {"service_level": [0.85, 0.9], "max_occupancy": [0.8]}
service_level_arguments = {"positions": [10, 20, 30], "scale_positions": [True, False]}

multi_erlang = MultiErlangC(param_grid=param_grid, n_jobs=4)

required_positions_grid = multi_erlang.required_positions(arguments_grid=required_positions_arguments)
print(required_positions_grid)

service_level_grid = multi_erlang.service_level(arguments_grid=service_level_arguments)
print(service_level_grid)
