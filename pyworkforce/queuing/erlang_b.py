"""Erlang B (M/M/c/c) pure-loss queue.

Erlang B models a system where there is **no waiting room**: if all *c* servers
(trunks, channels, agents) are busy when a call arrives, the call is
**blocked** and lost.  This is the right model for:

* **Trunk / channel sizing** – how many PSTN lines or SIP trunks are needed so
  that fewer than *x*% of calls receive a busy signal?
* **Circuit-switching capacity planning** in telecom networks.
* Any operation where excess demand is shed rather than queued (overflow groups,
  skill-based routing overflow links, …).

If customers can wait in a queue, use :class:`pyworkforce.queuing.ErlangC`
(infinite patience) or :class:`pyworkforce.queuing.ErlangA` (finite patience).
"""

from math import ceil, floor

from joblib import Parallel, delayed

from pyworkforce.base import BaseWorkforce
from pyworkforce.utils import ParameterGrid
from pyworkforce.utils.validation import check_in_range, check_positive_float


class ErlangB(BaseWorkforce):
    """
    Staffing and performance metrics for an Erlang B (M/M/c/c) loss queue.

    The blocking probability is computed exactly via the numerically stable
    Erlang B recursion, which avoids factorial overflow for large *c*.

    Parameters
    ----------
    transactions : float
        Total number of calls (or tasks) arriving in the interval.
    aht : float
        Average handling time in minutes.
    interval : int
        Interval length in minutes.
    shrinkage : float, default 0.0
        Fraction of time a position is unavailable (breaks, admin, …),
        in ``[0, 1)``.  Applied only when sizing the raw headcount returned
        by :meth:`required_positions`.

    Attributes
    ----------
    intensity : float
        Offered traffic in Erlangs: ``transactions / interval * aht``.

    Notes
    -----
    Unlike Erlang C, Erlang B is stable for **any** load — excess traffic is
    simply blocked.  There is therefore no requirement that *c* > *A*.

    Examples
    --------
    >>> from pyworkforce.queuing import ErlangB
    >>> erlang = ErlangB(transactions=100, aht=3, interval=30, shrinkage=0.3)
    >>> result = erlang.required_positions(max_blocking=0.02)
    >>> result["raw_positions"]
    17
    >>> result["positions"]
    25
    """

    def __init__(self, transactions: float, aht: float, interval: int,
                 shrinkage: float = 0.0):

        check_positive_float("transactions", transactions)
        check_positive_float("aht", aht)
        check_positive_float("interval", interval)
        check_in_range("shrinkage", shrinkage, 0, 1, include_high=False)

        self.transactions = transactions
        self.aht = aht
        self.interval = interval
        self.shrinkage = shrinkage
        self.intensity = (self.transactions / self.interval) * self.aht

    def _productive_positions(self, positions: int, scale_positions: bool = False) -> int:
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        if productive_positions <= 0:
            raise ValueError("productive positions must be greater than 0")

        return productive_positions

    def _erlang_b(self, productive_positions: int) -> float:
        """Blocking probability via the numerically stable recursion.

        B(0, A) = 1
        B(n, A) = A * B(n-1, A) / (n + A * B(n-1, A))
        """
        b = 1.0
        for n in range(1, productive_positions + 1):
            b = (self.intensity * b) / (n + self.intensity * b)
        return b

    def blocking_probability(self, positions: int, scale_positions: bool = False) -> float:
        """Probability that an arriving call is blocked (all trunks busy).

        Parameters
        ----------
        positions : int
            Number of trunks / channels / positions available.
        scale_positions : bool, default False
            Set to ``True`` when *positions* already includes the shrinkage
            padding (i.e. productive positions = ``floor((1−shrinkage) × positions)``).

        Returns
        -------
        float
            Blocking probability in ``[0, 1]``.
        """
        productive_positions = self._productive_positions(positions, scale_positions)
        return self._erlang_b(productive_positions)

    def achieved_occupancy(self, positions: int, scale_positions: bool = False) -> float:
        """Expected fraction of busy servers (server utilisation).

        Occupancy = carried traffic / number of servers
                  = A × (1 − B) / c

        Parameters
        ----------
        positions : int
            Number of trunks / channels / positions.
        scale_positions : bool, default False
            Set to ``True`` when *positions* already includes the shrinkage
            padding.
        """
        productive_positions = self._productive_positions(positions, scale_positions)
        b = self._erlang_b(productive_positions)
        return self.intensity * (1 - b) / productive_positions

    def required_positions(self, max_blocking: float, max_occupancy: float = 1.0) -> dict:
        """Minimum number of positions to stay within the blocking target.

        Parameters
        ----------
        max_blocking : float
            Maximum acceptable blocking probability, in ``[0, 1]``.
        max_occupancy : float, default 1.0
            Maximum acceptable occupancy, in ``(0, 1]``.

        Returns
        -------
        dict
            ``raw_positions``
                Positions required before applying shrinkage.
            ``positions``
                Positions after applying shrinkage:
                ``ceil(raw_positions / (1 − shrinkage))``.
            ``blocking_probability``
                Achieved blocking probability at *raw_positions*.
            ``occupancy``
                Achieved occupancy at *raw_positions*.
        """
        check_in_range("max_blocking", max_blocking, 0, 1)
        check_in_range("max_occupancy", max_occupancy, 0, 1, include_low=False)

        positions = 1
        while True:
            b = self._erlang_b(positions)
            occupancy = self.intensity * (1 - b) / positions
            if b <= max_blocking and occupancy <= max_occupancy:
                break
            positions += 1

        raw_positions = positions
        scaled_positions = ceil(raw_positions / (1 - self.shrinkage))

        return {
            "raw_positions": raw_positions,
            "positions": scaled_positions,
            "blocking_probability": self._erlang_b(raw_positions),
            "occupancy": self.intensity * (1 - self._erlang_b(raw_positions)) / raw_positions,
        }


class MultiErlangB(BaseWorkforce):
    """
    Runs Erlang B calculations over multiple parameter combinations.

    This class uses joblib's ``Parallel`` to evaluate every combination from
    ``param_grid`` and the method-specific argument grid.  Its interface
    mirrors :class:`pyworkforce.queuing.MultiErlangC`.

    Parameters
    ----------
    param_grid : dict
        :class:`ErlangB` constructor parameters; each value is a list.
        Example::

            {
                "transactions": [100, 200],
                "aht": [3],
                "interval": [30],
                "shrinkage": [0.0],
            }

    n_jobs : int, default 2
        Number of parallel workers (``-1`` = all CPUs, ``1`` = sequential).
    pre_dispatch : str or int, default ``'2 * n_jobs'``
        Task batches to pre-dispatch. See joblib's documentation.

    Attributes
    ----------
    blocking_probability_params, achieved_occupancy_params,
    required_positions_params : list[tuple] or None
        ``(erlang_params, method_params)`` for each result, in result order.
        Populated after the corresponding method is called.
    """

    def __init__(self, param_grid: dict, n_jobs: int = 2,
                 pre_dispatch: str = "2 * n_jobs"):
        self.param_grid = param_grid
        self.n_jobs = n_jobs
        self.pre_dispatch = pre_dispatch
        self.param_list = list(ParameterGrid(self.param_grid))
        self.blocking_probability_params = None
        self.achieved_occupancy_params = None
        self.required_positions_params = None

    def _solve(self, method_name, arguments_grid):
        """Evaluate *method_name* over the Cartesian product of both grids."""
        arguments_list = list(ParameterGrid(arguments_grid))
        used_params = [
            (erlang_params, method_params)
            for erlang_params in self.param_list
            for method_params in arguments_list
        ]
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs, pre_dispatch=self.pre_dispatch)(
            delayed(getattr(ErlangB(**params), method_name))(**arguments)
            for params in self.param_list
            for arguments in arguments_list
        )
        self._check_solutions(results, combinations)
        return results, used_params

    def blocking_probability(self, arguments_grid: dict) -> list:
        """Blocking probability for every grid combination.

        ``arguments_grid`` example: ``{"positions": [10, 15, 20]}``.
        """
        results, self.blocking_probability_params = self._solve("blocking_probability", arguments_grid)
        return results

    def achieved_occupancy(self, arguments_grid: dict) -> list:
        """Server occupancy for every grid combination.

        ``arguments_grid`` example: ``{"positions": [10, 15, 20]}``.
        """
        results, self.achieved_occupancy_params = self._solve("achieved_occupancy", arguments_grid)
        return results

    def required_positions(self, arguments_grid: dict) -> list:
        """Required positions for every grid combination.

        ``arguments_grid`` example:
        ``{"max_blocking": [0.01, 0.02], "max_occupancy": [0.8]}``.
        """
        results, self.required_positions_params = self._solve("required_positions", arguments_grid)
        return results

    def _check_solutions(self, solutions, combinations):
        if len(solutions) < 1:
            raise ValueError(
                "Could not find any solution; make sure the param_grid is defined correctly"
            )
        if len(solutions) != combinations:
            raise ValueError(
                f"Inconsistent results. Expected {combinations} solutions, got {len(solutions)}"
            )
