from math import exp, ceil, floor
from pyworkforce.utils import ParameterGrid
from joblib import Parallel, delayed


import numpy as np
from math import exp, gamma

class ErlangC:
    """
    Computes the number of positions required to attend a number of transactions in a
    queue system based on erlangc.rst. Implementation inspired on:
    https://lucidmanager.org/data-science/call-centre-workforce-planning-erlang-c-in-r/ and 
    https://www.callcentrehelper.com/erlang-c-formula-example-121281.htm
    Adaptiation to use gamma for non interger factorial usage.

    Parameters
    ----------
    transactions: float,
        The number of total transactions that comes in an interval.
    aht: float,
        Average handling time of a transaction (minutes).
    asa: float,
        The required average speed of answer (minutes).
    interval: int,
        Interval length (minutes) where the transactions come in
    shrinkage: float,
        Percentage of time that an operator unit is not available.
    """

    def __init__(self, transactions: float, aht: float, asa: float,
                 interval: int, shrinkage=0.0,
                 **kwargs):

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

    def waiting_probability(self, positions: float):
        """
        Returns the probability of waiting in the queue

        Parameters
        ----------
        positions: int,
            The number of positions to attend the transactions.

        """
        # Gamma distribution is extended to treat floats with factorials with n+1, this is the upper part of the erlang C equation
        substitution_position_estimate = (self.intensity**positions / gamma(positions+1)) * (positions / (positions-self.intensity) )

        #Sum of erlang series
        erlang_b = 1
        for position in np.arange(1, positions, 1):
            erlang_b += (self.intensity**position) / gamma(position+1)
        
        return substitution_position_estimate / (erlang_b + substitution_position_estimate)

    def service_level(self, positions: float):
        """
        Returns the expected service level given a number of positions

        Parameters
        ----------

        positions: int,
            The number of positions attending.
        scale_positions: bool, default = False
            Set it to True if the positions were calculated using shrinkage.

        """

        probability_wait = self.waiting_probability(positions)
        exponential = exp(-(positions - self.intensity) * (self.asa / self.aht))

        return max(0, 1-(probability_wait * exponential))

    def achieved_occupancy(self, positions: int):
        """
        Returns the expected occupancy of positions

        Parameters
        ----------

        positions: int,
            The number of raw positions

        """

        return self.intensity / positions

    def required_positions(self, service_level: float, max_occupancy: float = 1.0):
        """
        Computes the requirements using erlangc.rst

        Parameters
        ----------

        service_level: float,
            Target service level
        max_occupancy: float,
            The maximum fraction of time that a transaction can occupy a position

        Returns
        -------

        raw_positions: int,
            The required positions assuming shrinkage = 0
        positions: int,
            The number of positions needed to ensure the required service level
        service_level: float,
            The fraction of transactions that are expected to be assigned to a position,
            before the asa time
        occupancy: float,
            The expected occupancy of positions
        waiting_probability: float,
            The probability of a transaction waiting in the queue
        """

        if service_level < 0 or service_level > 1:
            raise ValueError("service_level must be between 0 and 1")

        if max_occupancy < 0 or max_occupancy > 1:
            raise ValueError("max_occupancy must be between 0 and 1")
        
        # set positions is intensity + 1 for initalisation, otherwise equations will return 1 for SL.
        raw_positions = self.intensity + 1
        achieved_service_level = self.service_level(raw_positions)
        # Incremental increase of position estimate to reach service level
        while achieved_service_level < service_level:
            raw_positions += .1
            achieved_service_level = self.service_level(raw_positions)

        # Adjust estimate when max occopancy is reached
        achieved_occupancy = self.achieved_occupancy(raw_positions)
        if achieved_occupancy > max_occupancy:
            raw_positions = self.intensity / max_occupancy
            achieved_occupancy = self.achieved_occupancy(raw_positions)
            achieved_service_level = self.service_level(raw_positions)

        waiting_probability = self.waiting_probability(positions=raw_positions)
        raw_positions = raw_positions * .9 # compensation for erlang C overestimations of capacity.
        #Compensate calculated positions for shrinkage factor used.
        positions = raw_positions / (1 - self.shrinkage)

        return {"raw_positions": round(raw_positions, 2),
                "positions": round(positions, 2),
                "service_level": achieved_service_level,
                "occupancy": achieved_occupancy,
                "waiting_probability": waiting_probability}


class MultiErlangC:
    """
    This class uses the erlangc.rst class using joblib's Parallel,
    allowing to run multiple scenarios at once.
    It finds solutions iterating over all possible combinations provided by the users,
    inspired how Sklearn's Grid Search works

    Parameters
    ----------

    param_grid: dict,
        Dictionary with the erlangc.rst.__init__ parameters, each key of the dictionary must be the
        expected parameter and the value must be a list with the different options to iterate
        example: {"transactions": [100, 200], "aht": [3], "interval": [30], "asa": [20 / 60], "shrinkage": [0.3]}
    n_jobs: int, default=2
        The maximum number of concurrently running jobs.
        If -1 all CPUs are used. If 1 is given, no parallel computing code is used at all, which is useful for debugging.
        For n_jobs below -1, (n_cpus + 1 + n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are used.
        None is a marker for ‘unset’ that will be interpreted as n_jobs=1 (sequential execution)
        unless the call is performed under a parallel_backend() context manager that sets another value for n_jobs.
    pre_dispatch: {"all", int, or expression}, default='2 * n_jobs'
        The number of batches (of tasks) to be pre-dispatched. Default is ‘2*n_jobs’.
        See joblib's documentation for more details: https://joblib.readthedocs.io/en/latest/generated/joblib.Parallel.html

    Attributes
    ----------

    waiting_probability_params: list[tuple],
        Each tuple of the list represents the used parameters in param_grid for ErlangC and
        arguments_grid for waiting_probability method,corresponding to the same order returned
        by the MultiErlangC.waiting_probability method.
    service_level_params: list[tuple],
        Each tuple of the list represents the used parameters in param_grid for ErlangC and
        arguments_grid for service_level method,corresponding to the same order returned
        by the MultiErlangC.service_level method.
    achieved_occupancy_params: list[tuple],
        Each tuple of the list represents the used parameters in param_grid for ErlangC and
        arguments_grid for achieved_occupancy method,corresponding to the same order returned
        by the MultiErlangC.achieved_occupancy method.
    required_positions_params: list[tuple],
        Each tuple of the list represents the used parameters in param_grid for ErlangC and
        arguments_grid for required_positions method,corresponding to the same order returned
        by the MultiErlangC.required_positions method.
    """

    def __init__(self, param_grid: dict, n_jobs: int = 2, pre_dispatch: str = '2 * n_jobs'):

        self.param_grid = param_grid
        self.n_jobs = n_jobs
        self.pre_dispatch = pre_dispatch
        self.param_list = list(ParameterGrid(self.param_grid))
        self.waiting_probability_params = None
        self.service_level_params = None
        self.achieved_occupancy_params = None
        self.required_positions_params = None

    def waiting_probability(self, arguments_grid):
        """
        Returns the probability of waiting in the queue
        Returns a list with the solution to all the possible combinations from the arguments_grid
        and the erlangc.rst param_grid

        Parameters
        ----------

        arguments_grid: dict,
            Dictionary with the erlangc.rst.waiting_probability parameters,
            each key of the dictionary must be the expected parameter and
            the value must be a list with the different options to iterate
            example: {"positions": [10, 20, 30], "scale_positions": [True, False]}
        """

        arguments_list = list(ParameterGrid(arguments_grid))
        self.waiting_probability_params = [(erlang_params, wait_params)
                                           for erlang_params in self.param_list
                                           for wait_params in arguments_list]
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).waiting_probability)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self._check_solutions(results, combinations)

        return results

    def service_level(self, arguments_grid):
        """
        Returns the expected service level given a number of positions
        Returns a list with the solution to all the possible combinations from the arguments_grid
        and the erlangc.rst param_grid

        Parameters
        ----------

        arguments_grid: dict,
            Dictionary with the erlangc.rst.service_level parameters,
            each key of the dictionary must be the expected parameter and
            the value must be a list with the different options to iterate
            example: {"positions": [10, 20, 30], "scale_positions": [True, False]}

        """
        arguments_list = list(ParameterGrid(arguments_grid))
        self.service_level_params = [(erlang_params, sl_params)
                                     for erlang_params in self.param_list
                                     for sl_params in arguments_list]
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).service_level)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self._check_solutions(results, combinations)

        return results

    def achieved_occupancy(self, arguments_grid):
        """
        Returns the expected occupancy of positions
        Returns a list with the solution to all the possible combinations from the arguments_grid
        and the erlangc.rst param_grid

        Parameters
        ----------

        arguments_grid: dict,
            Dictionary with the erlangc.rst.achieved_occupancy parameters,
            each key of the dictionary must be the expected parameter and
            the value must be a list with the different options to iterate
            example: {"positions": [10, 20, 30], "scale_positions": [True, False]}
        """

        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).achieved_occupancy)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self._check_solutions(results, combinations)

        return results

    def required_positions(self, arguments_grid):
        """
        Computes the requirements using MultiErlangC
        Returns a list with the solution to all the possible combinations from the arguments_grid and the erlangc.rst param_grid

        Parameters
        ----------

        arguments_grid: dict,
            Dictionary with the erlangc.rst.achieved_occupancy parameters,
            each key of the dictionary must be the expected parameter and
            the value must be a list with the different options to iterate
            example: {"service_level": [0.85, 0.9], "max_occupancy": [0.8, 0.95]}
        """

        arguments_list = list(ParameterGrid(arguments_grid))
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs,
                           pre_dispatch=self.pre_dispatch)(delayed(ErlangC(**params).required_positions)(**arguments)
                                                           for params in self.param_list
                                                           for arguments in arguments_list)
        self._check_solutions(results, combinations)

        return results

    def _check_solutions(self, solutions, combinations):
        """
        Checks the integrity of the solution in terms of dimensions
        """
        if len(solutions) < 1:  # noqa
            raise ValueError("Could not find any solution, make sure the param_grid is defined correctly")

        if len(solutions) != combinations:
            raise ValueError('Inconsistent results. Expected {} '
                             'solutions, got {}'
                             .format(len(self.param_list),
                                     len(solutions))) # noqa