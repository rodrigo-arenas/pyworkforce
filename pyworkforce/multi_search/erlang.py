from sklearn.model_selection import ParameterGrid
from joblib import Parallel, delayed
from pyworkforce.queuing import ErlangC


class MultiErlangC:
    """
    This class uses de ErlangC class using joblib's Parallel allowing to run multiples scenarios with one class
    """

    def __init__(self, param_grid, n_jobs=2, pre_dispatch='2 * n_jobs'):
        """
        :param param_grid: Dictionary with the ErlangC.__init__ parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"transactions": [100, 200], "aht": [3], "interval": [30], "asa": [20 / 60], "shrinkage": [0.3]}
        :param n_jobs: The maximum number of concurrently running jobs
        :param pre_dispatch:The number of batches (of tasks) to be pre-dispatched. Default is ‘2*n_jobs’.
        See joblib's documentation for more details: https://joblib.readthedocs.io/en/latest/generated/joblib.Parallel.html
        """
        self.param_grid = param_grid
        self.n_jobs = n_jobs
        self.pre_dispatch = pre_dispatch
        self.param_list = list(ParameterGrid(self.param_grid))

    def waiting_probability(self, arguments_grid):
        """
        :param arguments_grid: Dictionary with the ErlangC.achieved_occupancy parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"positions": [10, 20, 30], "scale_positions": [True, False]}
        :return: A list with the solution to all the possible combinations from the arguments_grid and the ErlangC param_grid
        """
        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).waiting_probability)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self.check_solutions(results, combinations)

        return results

    def service_level(self, arguments_grid):
        """
        :param arguments_grid: Dictionary with the ErlangC.required_positions parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"positions": [10, 20, 30], "scale_positions": [True, False]}
        :return: A list with the solution to all the possible combinations from the arguments_grid and the ErlangC param_grid
        """
        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).service_level)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self.check_solutions(results, combinations)

        return results

    def achieved_occupancy(self, arguments_grid):
        """
        :param arguments_grid: Dictionary with the ErlangC.achieved_occupancy parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"positions": [10, 20, 30], "scale_positions": [True, False]}
        :return: A list with the solution to all the possible combinations from the arguments_grid and the ErlangC param_grid
        """
        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).achieved_occupancy)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self.check_solutions(results, combinations)

        return results

    def required_positions(self, arguments_grid):
        """
        :param arguments_grid: Dictionary with the ErlangC.required_positions parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"service_level": [0.85, 0.9], "max_occupancy": [0.8, 0.95]}
        :return: A list with the solution to all the possible combinations from the arguments_grid and the ErlangC param_grid
        """
        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).required_positions)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self.check_solutions(results, combinations)

        return results

    def check_solutions(self, solutions, combinations):
        if len(solutions) < 1:
            raise ValueError("Could not find any solution, make sure the param_grid is defined correctly")

        if len(solutions) != combinations:
            raise ValueError('Inconsistent results. Expected {} '
                             'solutions, got {}'
                             .format(len(self.param_list),
                                     len(solutions)))
