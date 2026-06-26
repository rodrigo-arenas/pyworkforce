"""Erlang A (M/M/c+M) queue with customer abandonment.

Erlang C assumes that customers wait indefinitely. In real contact centers
customers hang up if they wait too long. The Erlang A model adds an
*abandonment* (or *patience*) rate: every waiting customer leaves the queue
after an exponentially distributed patience time with mean ``patience``.

All performance metrics are computed exactly from the stationary distribution
of the underlying birth-death Markov chain, so there is no reliance on
closed-form approximations. The chain is positive recurrent for any load
because abandonment keeps the queue finite; the state space is truncated once
the tail probability is negligible.
"""

from math import ceil, exp

from joblib import Parallel, delayed

from pyworkforce.base import BaseWorkforce
from pyworkforce.utils import ParameterGrid
from pyworkforce.utils.validation import check_in_range, check_positive_float


class ErlangA(BaseWorkforce):
    """
    Staffing and performance metrics for an Erlang A (M/M/c+M) queue.

    Parameters
    ----------
    transactions: float,
        Total number of transactions arriving in the interval.
    aht: float,
        Average handling time of a transaction (minutes).
    asa: float,
        The required average speed of answer (minutes). Used as the default
        target when computing the service level.
    interval: int,
        Interval length, in minutes.
    patience: float,
        Average time (minutes) a customer waits before abandoning the queue.
        Smaller values mean less patient customers.
    shrinkage: float, default=0.0
        Fraction of time that an operator unit is not available, in ``[0, 1)``.

    Attributes
    ----------
    intensity: float,
        Offered traffic intensity in Erlangs (``transactions / interval * aht``).

    Notes
    -----
    As ``patience`` grows large (customers become infinitely patient) and the
    system is stable, the Erlang A metrics converge to the Erlang C results.

    Examples
    --------
    >>> from pyworkforce.queuing import ErlangA
    >>> erlang = ErlangA(transactions=100, aht=3, asa=20 / 60,
    ...                  interval=30, patience=5, shrinkage=0.0)
    >>> result = erlang.required_positions(service_level=0.8)
    >>> result["positions"] >= result["raw_positions"]
    True
    """

    def __init__(self, transactions: float, aht: float, asa: float,
                 interval: int, patience: float, shrinkage: float = 0.0):

        check_positive_float("transactions", transactions)
        check_positive_float("aht", aht)
        check_positive_float("asa", asa)
        check_positive_float("interval", interval)
        check_positive_float("patience", patience)
        check_in_range("shrinkage", shrinkage, 0, 1, include_high=False)

        self.transactions = transactions
        self.aht = aht
        self.asa = asa
        self.interval = interval
        self.patience = patience
        self.shrinkage = shrinkage

        # Rates expressed per minute.
        self.arrival_rate = transactions / interval
        self.service_rate = 1.0 / aht
        self.abandonment_rate = 1.0 / patience
        self.intensity = self.arrival_rate / self.service_rate

    def _stationary_distribution(self, positions):
        """Return the normalized stationary distribution ``p[n]`` for ``c`` servers.

        The birth-death chain has birth rate ``arrival_rate`` and death rate
        ``min(n, c) * service_rate + max(n - c, 0) * abandonment_rate``. The
        state space is grown until the unnormalized tail is negligible.
        """
        c = positions
        lam = self.arrival_rate
        mu = self.service_rate
        theta = self.abandonment_rate

        probs = [1.0]
        total = 1.0
        n = 0
        # Grow the chain until the newest term is a negligible fraction of the
        # accumulated mass (and we are safely beyond the number of servers).
        while True:
            n += 1
            death_rate = (n if n <= c else c) * mu + (max(n - c, 0)) * theta
            term = probs[-1] * lam / death_rate
            probs.append(term)
            total += term
            if n > c and term < 1e-15 * total:
                break
            if n > c + 100000:  # pragma: no cover - safety guard, should never trigger
                break
            # Rescale to avoid overflow for very heavy traffic.
            if probs[-1] > 1e250:  # pragma: no cover - overflow guard for extreme load
                probs = [p / 1e250 for p in probs]
                total /= 1e250

        norm = sum(probs)
        return [p / norm for p in probs]

    def _metrics(self, positions):
        """Compute the core stationary metrics for ``positions`` servers."""
        c = positions
        probs = self._stationary_distribution(c)

        wait_probability = sum(probs[n] for n in range(c, len(probs)))
        queue_length = sum((n - c) * probs[n] for n in range(c, len(probs)))
        abandonment_probability = (self.abandonment_rate * queue_length) / self.arrival_rate
        throughput = self.arrival_rate * (1 - abandonment_probability)
        occupancy = throughput / (c * self.service_rate)
        average_speed_of_answer = queue_length / self.arrival_rate

        return {
            "probs": probs,
            "waiting_probability": wait_probability,
            "abandonment_probability": abandonment_probability,
            "occupancy": occupancy,
            "average_queue_length": queue_length,
            "average_speed_of_answer": average_speed_of_answer,
        }

    def waiting_probability(self, positions: int):
        """Probability that an arriving transaction has to wait (is delayed).

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        """
        self._check_positions(positions)
        return self._metrics(positions)["waiting_probability"]

    def abandonment_probability(self, positions: int):
        """Probability that an arriving transaction eventually abandons.

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        """
        self._check_positions(positions)
        return self._metrics(positions)["abandonment_probability"]

    def achieved_occupancy(self, positions: int):
        """Expected fraction of busy positions (server utilization).

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        """
        self._check_positions(positions)
        return self._metrics(positions)["occupancy"]

    def average_speed_of_answer(self, positions: int):
        """Expected waiting time (minutes) averaged over all transactions.

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        """
        self._check_positions(positions)
        return self._metrics(positions)["average_speed_of_answer"]

    def average_queue_length(self, positions: int):
        """Expected number of transactions waiting in queue.

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        """
        self._check_positions(positions)
        return self._metrics(positions)["average_queue_length"]

    def service_level(self, positions: int, asa: float = None):
        """Fraction of transactions answered within ``asa`` minutes.

        A non-delayed transaction is answered immediately. For delayed
        transactions, the probability of being served within ``asa`` is computed
        exactly from the tagged-customer absorbing Markov chain (a customer in
        queue position ``j`` advances at rate ``c * service_rate + j *
        abandonment_rate`` and abandons at rate ``abandonment_rate``) using
        uniformization.

        Parameters
        ----------
        positions: int,
            Number of available positions (servers).
        asa: float, optional
            Target answer time in minutes. Defaults to the ``asa`` given at
            construction time.
        """
        self._check_positions(positions)
        if asa is None:
            asa = self.asa
        check_positive_float("asa", asa)

        c = positions
        metrics = self._metrics(c)
        probs = metrics["probs"]

        served_immediately = sum(probs[:c])
        delayed_states = list(range(c, len(probs)))
        if not delayed_states:  # pragma: no cover - the chain always extends past c
            return served_immediately

        max_ahead = len(probs) - 1 - c  # maximum queue position a customer can take
        served_within = self._delayed_served_within(c, max_ahead, asa)

        delayed_served = 0.0
        for n in delayed_states:
            ahead = n - c
            delayed_served += probs[n] * served_within[ahead]

        return min(1.0, served_immediately + delayed_served)

    def _delayed_served_within(self, c, max_ahead, t):
        """Return ``G[j]`` = P(tagged customer with ``j`` ahead is served by ``t``).

        Uses uniformization of the tagged-customer CTMC with absorbing states
        ``served`` and ``abandoned``.
        """
        mu = self.service_rate
        states = max_ahead + 1  # j = 0 .. max_ahead

        # Uniformization rate: maximum total outflow across transient states.
        max_rate = c * mu + max_ahead * self.abandonment_rate + self.abandonment_rate
        if max_rate <= 0:  # pragma: no cover - rates are always strictly positive
            return [0.0] * states

        # The tagged chain is lower-triangular (queue position only decreases),
        # so we solve the transient absorption once per starting position.
        served = [0.0] * states
        for start in range(states):
            served[start] = self._uniformized_served_prob(start, c, max_ahead, t, max_rate)
        return served

    def _uniformized_served_prob(self, start, c, max_ahead, t, max_rate):
        """P(absorbed into 'served' by time ``t``) starting at queue position ``start``."""
        mu = self.service_rate
        theta = self.abandonment_rate
        states = max_ahead + 1

        # Distribution over transient states, plus accumulated absorbed-served mass.
        dist = [0.0] * states
        dist[start] = 1.0
        served_mass = 0.0

        lam_t = max_rate * t
        # Poisson weights of the uniformized chain; truncate when tail is tiny.
        # Number of steps: mean lam_t plus margin.
        max_steps = int(lam_t + 10 * (lam_t ** 0.5) + 50)

        poisson = exp(-lam_t)  # P(N = 0)
        result = poisson * served_mass  # contribution from 0 jumps (no absorption yet)
        for k in range(1, max_steps + 1):
            # Advance the uniformized DTMC one step.
            new_dist = [0.0] * states
            for j in range(states):
                pj = dist[j]
                if pj == 0.0:
                    continue
                if j == 0:
                    success_rate = c * mu
                    abandon_rate = theta
                    stay_rate = max_rate - success_rate - abandon_rate
                    served_mass += pj * (success_rate / max_rate)
                    # abandon mass is simply lost (absorbed into fail)
                    new_dist[0] += pj * (stay_rate / max_rate)
                else:
                    advance_rate = c * mu + j * theta
                    abandon_rate = theta
                    stay_rate = max_rate - advance_rate - abandon_rate
                    new_dist[j - 1] += pj * (advance_rate / max_rate)
                    new_dist[j] += pj * (stay_rate / max_rate)
            dist = new_dist

            poisson *= lam_t / k  # P(N = k)
            result += poisson * served_mass

        return result

    def required_positions(self, service_level: float, max_occupancy: float = 1.0,
                           max_abandonment: float = 1.0, asa: float = None):
        """Smallest number of positions meeting the target service level.

        Parameters
        ----------
        service_level: float,
            Target fraction of transactions answered within ``asa``, in ``[0, 1]``.
        max_occupancy: float, default=1.0
            Maximum allowed server occupancy, in ``(0, 1]``.
        max_abandonment: float, default=1.0
            Maximum allowed abandonment probability, in ``[0, 1]``.
        asa: float, optional
            Target answer time in minutes. Defaults to the construction ``asa``.

        Returns
        -------
        dict
            Keys: ``raw_positions`` (before shrinkage), ``positions`` (after
            shrinkage), ``service_level``, ``occupancy``,
            ``abandonment_probability``, ``waiting_probability`` and
            ``average_speed_of_answer``.
        """
        check_in_range("service_level", service_level, 0, 1)
        check_in_range("max_occupancy", max_occupancy, 0, 1, include_low=False)
        check_in_range("max_abandonment", max_abandonment, 0, 1)
        if asa is None:
            asa = self.asa

        positions = max(1, int(ceil(self.intensity)))
        while True:
            metrics = self._metrics(positions)
            achieved_sl = self.service_level(positions, asa=asa)
            if (achieved_sl >= service_level
                    and metrics["occupancy"] <= max_occupancy
                    and metrics["abandonment_probability"] <= max_abandonment):
                break
            positions += 1
            if positions > self.intensity + 100000:  # pragma: no cover - safety guard
                break

        raw_positions = positions
        scaled_positions = int(ceil(raw_positions / (1 - self.shrinkage)))
        metrics = self._metrics(raw_positions)

        return {
            "raw_positions": raw_positions,
            "positions": scaled_positions,
            "service_level": self.service_level(raw_positions, asa=asa),
            "occupancy": metrics["occupancy"],
            "abandonment_probability": metrics["abandonment_probability"],
            "waiting_probability": metrics["waiting_probability"],
            "average_speed_of_answer": metrics["average_speed_of_answer"],
        }

    @staticmethod
    def _check_positions(positions):
        if isinstance(positions, bool) or not isinstance(positions, int) or positions <= 0:
            raise ValueError(f"positions must be a positive integer, got {positions!r}")


class MultiErlangA(BaseWorkforce):
    """
    Runs Erlang A calculations over multiple parameter combinations.

    This is the abandonment-aware counterpart of
    :class:`pyworkforce.queuing.MultiErlangC`. It evaluates every combination
    from ``param_grid`` and the method-specific argument grid in parallel using
    joblib, with a scikit-learn-like interface.

    Parameters
    ----------
    param_grid: dict,
        Dictionary with :class:`ErlangA` initialization parameters. Each key
        must be an expected parameter, and each value must be a list of options
        to iterate over.
        example: {"transactions": [100, 200], "aht": [3], "interval": [30],
        "asa": [20 / 60], "patience": [5], "shrinkage": [0.3]}
    n_jobs: int, default=2
        Maximum number of concurrently running jobs. ``-1`` uses all CPUs,
        ``1`` disables parallelism (useful for debugging).
    pre_dispatch: {"all", int, or expression}, default='2 * n_jobs'
        Number of task batches to pre-dispatch. See joblib's documentation.

    Attributes
    ----------
    waiting_probability_params, abandonment_probability_params,
    achieved_occupancy_params, average_speed_of_answer_params,
    average_queue_length_params, service_level_params,
    required_positions_params: list[tuple],
        Parameters used for each result of the matching method, in result
        order. Each entry is an ``(erlang_params, method_params)`` tuple.
    """

    def __init__(self, param_grid: dict, n_jobs: int = 2, pre_dispatch: str = '2 * n_jobs'):
        self.param_grid = param_grid
        self.n_jobs = n_jobs
        self.pre_dispatch = pre_dispatch
        self.param_list = list(ParameterGrid(self.param_grid))
        self.waiting_probability_params = None
        self.abandonment_probability_params = None
        self.achieved_occupancy_params = None
        self.average_speed_of_answer_params = None
        self.average_queue_length_params = None
        self.service_level_params = None
        self.required_positions_params = None

    def _solve(self, method_name, arguments_grid):
        """Evaluate ``method_name`` over the cartesian product of both grids.

        Returns
        -------
        tuple(list, list)
            The list of results and the parallel list of
            ``(erlang_params, method_params)`` tuples that produced them.
        """
        arguments_list = list(ParameterGrid(arguments_grid))
        used_params = [(erlang_params, method_params)
                       for erlang_params in self.param_list
                       for method_params in arguments_list]
        combinations = len(self.param_list) * len(arguments_list)
        results = Parallel(n_jobs=self.n_jobs, pre_dispatch=self.pre_dispatch)(
            delayed(getattr(ErlangA(**params), method_name))(**arguments)
            for params in self.param_list
            for arguments in arguments_list)
        self._check_solutions(results, combinations)
        return results, used_params

    def waiting_probability(self, arguments_grid):
        """Probability of waiting for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14, 16]}``.
        """
        results, self.waiting_probability_params = self._solve("waiting_probability", arguments_grid)
        return results

    def abandonment_probability(self, arguments_grid):
        """Abandonment probability for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14, 16]}``.
        """
        results, self.abandonment_probability_params = self._solve("abandonment_probability", arguments_grid)
        return results

    def achieved_occupancy(self, arguments_grid):
        """Server occupancy for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14, 16]}``.
        """
        results, self.achieved_occupancy_params = self._solve("achieved_occupancy", arguments_grid)
        return results

    def average_speed_of_answer(self, arguments_grid):
        """Average speed of answer for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14, 16]}``.
        """
        results, self.average_speed_of_answer_params = self._solve("average_speed_of_answer", arguments_grid)
        return results

    def average_queue_length(self, arguments_grid):
        """Average queue length for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14, 16]}``.
        """
        results, self.average_queue_length_params = self._solve("average_queue_length", arguments_grid)
        return results

    def service_level(self, arguments_grid):
        """Service level for every grid combination.

        ``arguments_grid`` example: ``{"positions": [12, 14], "asa": [20 / 60]}``.
        """
        results, self.service_level_params = self._solve("service_level", arguments_grid)
        return results

    def required_positions(self, arguments_grid):
        """Required positions for every grid combination.

        ``arguments_grid`` example:
        ``{"service_level": [0.8, 0.9], "max_occupancy": [0.85], "max_abandonment": [0.05]}``.
        """
        results, self.required_positions_params = self._solve("required_positions", arguments_grid)
        return results

    def _check_solutions(self, solutions, combinations):
        """Check the integrity of the solution in terms of dimensions."""
        if len(solutions) < 1:
            raise ValueError("Could not find any solution, make sure the param_grid is defined correctly")
        if len(solutions) != combinations:
            raise ValueError(f"Inconsistent results. Expected {combinations} solutions, got {len(solutions)}")
