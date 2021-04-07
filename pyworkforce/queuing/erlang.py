from math import exp, ceil, floor
from sklearn.model_selection import ParameterGrid
from joblib import Parallel, delayed


class ErlangC:
    def __init__(self, transactions: float, aht: float, asa: float,
                 interval: int = None, shrinkage=0.0,
                 **kwargs):
        """
        Computes the number of positions required fo attend a number of transactions in a queue system based on ErlangC
        Implementation based on: https://lucidmanager.org/data-science/call-centre-workforce-planning-erlang-c-in-r/

        :param transactions: number of total transactions that comes in an interval
        :param aht: average handling time of a transaction (minutes)
        :param asa: Required average speed of answer in minutes
        :param interval: Interval length (minutes)
        :param shrinkage: Percentage of time that an operator unit is not available
        """

        if transactions <= 0:
            raise ValueError("transactions can't be smaller or equals than 0")

        if aht <= 0:
            raise ValueError("aht can't be smaller or equals than 0")

        if asa <= 0:
            raise ValueError("asa can't be smaller or equals than 0")

        if interval <= 0:
            raise ValueError("interval can't be smaller or equals than 0")

        if shrinkage < 0 or shrinkage >= 1:
            raise ValueError("shrinkage must be between in the interval [0,1)")

        self.n_transactions = transactions
        self.aht = aht
        self.interval = interval
        self.asa = asa
        self.intensity = (self.n_transactions / self.interval) * self.aht
        self.shrinkage = shrinkage

    def waiting_probability(self, positions, scale_positions=False):
        """
        :param positions: Number of positions to attend the transactions
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: the probability of a transaction waits in queue
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        erlang_b_inverse = 1
        for position in range(1, productive_positions + 1):
            erlang_b_inverse = 1 + (erlang_b_inverse * position / self.intensity)

        erlang_b = 1 / erlang_b_inverse
        return productive_positions * erlang_b / (productive_positions - self.intensity * (1 - erlang_b))

    def service_level(self, positions, scale_positions=False):
        """
        :param positions: Number of positions attending
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: achieved service level
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        probability_wait = self.waiting_probability(productive_positions, scale_positions=False)
        exponential = exp(-(productive_positions - self.intensity) * (self.asa / self.aht))
        return max(0, 1 - (probability_wait * exponential))

    def achieved_occupancy(self, positions, scale_positions=False):
        """
        :param positions: Number of raw positions
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: Expected occupancy of positions
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        return self.intensity / productive_positions

    def required_positions(self, service_level: float, max_occupancy: float = 1.0):
        """
        :param service_level: Target service level
        :param max_occupancy: Maximum fraction of time that an attending position can be occupied
        :return:
                 * raw_positions: Required positions assuming shrinkage = 0
                 * positions: Number of positions needed to ensure the required service level
                 * service_level: Fraction of transactions that are expect to be assigned to a position,
                   before the asa time
                 * occupancy: Expected occupancy of positions
                 * waiting_probability: The probability of a transaction waits in queue
        """

        if service_level < 0 or service_level > 1:
            raise ValueError("service_level must be between 0 and 1")

        if max_occupancy < 0 or max_occupancy > 1:
            raise ValueError("max_occupancy must be between 0 and 1")

        positions = round(self.intensity + 1)
        achieved_service_level = self.service_level(positions, scale_positions=False)
        while achieved_service_level < service_level:
            positions += 1
            achieved_service_level = self.service_level(positions, scale_positions=False)

        achieved_occupancy = self.achieved_occupancy(positions, scale_positions=False)

        raw_positions = ceil(positions)

        if achieved_occupancy > max_occupancy:
            raw_positions = ceil(self.intensity / max_occupancy)
            achieved_occupancy = self.achieved_occupancy(raw_positions)
            achieved_service_level = self.service_level(raw_positions)

        waiting_probability = self.waiting_probability(positions=raw_positions)
        positions = ceil(raw_positions / (1 - self.shrinkage))

        return {"raw_positions": raw_positions,
                "positions": positions,
                "service_level": achieved_service_level,
                "occupancy": achieved_occupancy,
                "waiting_probability": waiting_probability}


class MultiErlangC:
    """
    This class uses de ErlangC class using joblib's Parallel allowing to run multiples scenarios with one class It
    finds solutions iterating over all possible combinations provided by the users, inspired how Sklearn's Grid
    Search works
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
