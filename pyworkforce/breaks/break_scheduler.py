from ortools.sat.python import cp_model

from pyworkforce.base import BaseWorkforce
from pyworkforce.utils.validation import check_positive_float, check_positive_integer


class BreakScheduler(BaseWorkforce):
    """
    Schedules breaks for agent slots within each shift to maintain minimum
    coverage throughout the planning horizon.

    Each shift/day combination has ``scheduled_resources[shift][day]`` anonymous
    agent slots. The solver assigns a start period to every break for every slot
    while enforcing:

    * **Break window** – each break must start at least ``min_start_after``
      periods into the shift and must finish at least ``max_end_before`` periods
      before the shift ends.
    * **No overlap** – two breaks assigned to the same slot cannot overlap.
    * **Coverage** – at every period the number of agents *on break* must not
      exceed ``total_scheduled − min_coverage``.

    Parameters
    ----------
    num_days : int
        Number of days in the planning horizon.
    periods : int
        Number of periods per day (e.g. 48 for 30-minute slots in a 24-hour day).
    shifts_coverage : dict
        ``{"shift_name": coverage_array}`` where ``coverage_array`` has length
        ``periods`` and uses 1 when the shift is active, otherwise 0.
    scheduled_resources : dict
        ``{"shift_name": [count_day0, count_day1, …]}`` — number of agent slots
        per shift per day (typically the output of the scheduling step).
    breaks : list[dict]
        Each element defines one break type::

            {
                "name":             str,   # unique identifier
                "duration_periods": int,   # length of the break in periods
                "min_start_after":  int,   # periods into shift before break may start (default 0)
                "max_end_before":   int,   # periods remaining after break must end (default 0)
            }

    min_coverage : list
        2-D array ``[num_days][periods]`` — minimum agents that must remain
        available (not on break) at each period.  Pass the same
        ``required_resources`` array used in the scheduling step to preserve
        the service level agreed there.
    max_search_time : float, default 120.0
        Maximum solver wall-clock time in seconds.
    num_search_workers : int, default 2
        Number of parallel search workers.

    Attributes
    ----------
    solution_ : dict or None
        Populated by :meth:`solve`.

    Examples
    --------
    >>> from pyworkforce.breaks import BreakScheduler
    >>> shifts_coverage = {"Morning": [0, 0, 1, 1, 1, 1, 1, 1, 0, 0]}
    >>> scheduled_resources = {"Morning": [5]}
    >>> breaks = [{"name": "Lunch", "duration_periods": 1,
    ...            "min_start_after": 1, "max_end_before": 1}]
    >>> min_coverage = [[0, 0, 3, 3, 3, 3, 3, 3, 0, 0]]
    >>> scheduler = BreakScheduler(
    ...     num_days=1, periods=10,
    ...     shifts_coverage=shifts_coverage,
    ...     scheduled_resources=scheduled_resources,
    ...     breaks=breaks,
    ...     min_coverage=min_coverage,
    ... )
    >>> result = scheduler.solve()
    >>> result["status"] in ("OPTIMAL", "FEASIBLE")
    True
    """

    def __init__(
        self,
        num_days: int,
        periods: int,
        shifts_coverage: dict,
        scheduled_resources: dict,
        breaks: list,
        min_coverage: list,
        max_search_time: float = 120.0,
        num_search_workers: int = 2,
    ):
        check_positive_integer("num_days", num_days)
        check_positive_integer("periods", periods)
        check_positive_float("max_search_time", max_search_time)
        check_positive_integer("num_search_workers", num_search_workers)

        if not shifts_coverage:
            raise ValueError("shifts_coverage must not be empty")

        missing = set(shifts_coverage) - set(scheduled_resources)
        if missing:
            raise ValueError(f"scheduled_resources is missing keys for shifts: {sorted(missing)}")

        extra = set(scheduled_resources) - set(shifts_coverage)
        if extra:
            raise ValueError(f"scheduled_resources contains unknown shifts: {sorted(extra)}")

        for s, counts in scheduled_resources.items():
            if len(counts) != num_days:
                raise ValueError(
                    f"scheduled_resources['{s}'] has length {len(counts)}, expected {num_days}"
                )

        for s, cov in shifts_coverage.items():
            if len(cov) != periods:
                raise ValueError(
                    f"shifts_coverage['{s}'] has length {len(cov)}, expected {periods}"
                )

        if len(min_coverage) != num_days:
            raise ValueError(f"min_coverage has {len(min_coverage)} rows, expected {num_days}")
        for d, row in enumerate(min_coverage):
            if len(row) != periods:
                raise ValueError(f"min_coverage[{d}] has length {len(row)}, expected {periods}")

        if not breaks:
            raise ValueError("breaks must not be empty")

        break_names = [b.get("name") for b in breaks]
        if any(n is None for n in break_names):
            raise ValueError("every break must have a 'name' key")
        if len(break_names) != len(set(break_names)):
            raise ValueError("break names must be unique")

        for b in breaks:
            if "duration_periods" not in b:
                raise ValueError(f"break '{b['name']}' is missing 'duration_periods'")
            check_positive_integer(f"break '{b['name']}' duration_periods", b["duration_periods"])
            for field in ("min_start_after", "max_end_before"):
                val = b.get(field, 0)
                if val < 0:
                    raise ValueError(f"break '{b['name']}' {field} must be >= 0, got {val}")

        for s, cov in shifts_coverage.items():
            covered = [p for p, v in enumerate(cov) if v == 1]
            if not covered:
                raise ValueError(f"shift '{s}' has no active periods in shifts_coverage")
            s_len = covered[-1] - covered[0] + 1
            for b in breaks:
                min_after = b.get("min_start_after", 0)
                max_before = b.get("max_end_before", 0)
                dur = b["duration_periods"]
                if min_after + max_before + dur > s_len:
                    raise ValueError(
                        f"break '{b['name']}' (duration={dur}, min_start_after={min_after}, "
                        f"max_end_before={max_before}) cannot fit in shift '{s}' "
                        f"which spans {s_len} active periods"
                    )

        self.num_days = num_days
        self.periods = periods
        self.shifts_coverage = shifts_coverage
        self.scheduled_resources = scheduled_resources
        self.breaks = breaks
        self.min_coverage = min_coverage
        self.max_search_time = max_search_time
        self.num_search_workers = num_search_workers
        self.solution_ = None

    def solve(self) -> dict:
        """
        Run the CP-SAT solver to assign break start periods.

        Returns
        -------
        dict
            A dictionary with the following keys:

            ``status`` : str
                Solver status (``"OPTIMAL"``, ``"FEASIBLE"``, or
                ``"INFEASIBLE"``).
            ``cost`` : float
                Objective value (0.0 for feasible solutions; −1 when
                infeasible, since no objective is defined).
            ``break_schedule`` : list[dict]
                One entry per (shift, day, slot, break).  Each entry has
                ``shift``, ``day``, ``slot``, ``break_name``,
                ``start_period`` (inclusive), and ``end_period``
                (exclusive: ``start_period + duration_periods``).
        """
        sch_model = cp_model.CpModel()

        shift_start = {}
        shift_end = {}
        for s, cov in self.shifts_coverage.items():
            covered = [p for p, v in enumerate(cov) if v == 1]
            shift_start[s] = covered[0]
            shift_end[s] = covered[-1]

        break_by_name = {b["name"]: b for b in self.breaks}

        # Decision variables
        start_vars = {}    # (s, d, i, b_name) → IntVar
        interval_vars = {} # (s, d, i, b_name) → IntervalVar
        var_domains = {}   # (s, d, i, b_name) → (valid_lo, valid_hi)

        for s in self.shifts_coverage:
            s_start = shift_start[s]
            s_end = shift_end[s]

            for d in range(self.num_days):
                n_slots = self.scheduled_resources[s][d]

                for i in range(n_slots):
                    slot_ivars = []

                    for b in self.breaks:
                        b_name = b["name"]
                        dur = b["duration_periods"]
                        min_after = b.get("min_start_after", 0)
                        max_before = b.get("max_end_before", 0)

                        valid_lo = s_start + min_after
                        valid_hi = s_end - max_before - dur + 1

                        key = (s, d, i, b_name)
                        start_var = sch_model.NewIntVar(valid_lo, valid_hi, f"start_{s}_{d}_{i}_{b_name}")
                        end_var = sch_model.NewIntVar(valid_lo + dur, valid_hi + dur, f"end_{s}_{d}_{i}_{b_name}")
                        ivar = sch_model.NewIntervalVar(start_var, dur, end_var, f"ivar_{s}_{d}_{i}_{b_name}")

                        start_vars[key] = start_var
                        interval_vars[key] = ivar
                        var_domains[key] = (valid_lo, valid_hi)
                        slot_ivars.append(ivar)

                    if len(slot_ivars) > 1:
                        sch_model.AddNoOverlap(slot_ivars)

        # Precompute total scheduled agents per (day, period)
        total_scheduled = [[0] * self.periods for _ in range(self.num_days)]
        for s, cov in self.shifts_coverage.items():
            for d in range(self.num_days):
                n = self.scheduled_resources[s][d]
                for p in range(self.periods):
                    if cov[p] == 1:
                        total_scheduled[d][p] += n

        # Coverage constraints
        for d in range(self.num_days):
            for p in range(self.periods):
                sched_at_p = total_scheduled[d][p]
                if sched_at_p == 0:
                    continue

                min_cov = self.min_coverage[d][p]
                slack = sched_at_p - min_cov
                if slack < 0:
                    raise ValueError(
                        f"min_coverage[{d}][{p}]={min_cov} exceeds "
                        f"total scheduled={sched_at_p} at day={d}, period={p}"
                    )

                covers_vars = []

                for s, cov in self.shifts_coverage.items():
                    if cov[p] != 1:
                        continue
                    for i in range(self.scheduled_resources[s][d]):
                        for b in self.breaks:
                            b_name = b["name"]
                            dur = b["duration_periods"]
                            key = (s, d, i, b_name)
                            start_var = start_vars[key]
                            valid_lo, valid_hi = var_domains[key]

                            # break covers period p iff start ∈ [p - dur + 1, p]
                            window_lo = max(valid_lo, p - dur + 1)
                            window_hi = min(valid_hi, p)

                            if window_lo > window_hi:
                                continue  # break can never cover this period

                            covers = sch_model.NewBoolVar(f"cov_{s}_{d}_{i}_{b_name}_{p}")

                            can_be_before = window_lo > valid_lo
                            can_be_after = window_hi < valid_hi

                            if not can_be_before and not can_be_after:
                                # window == full domain: break always covers this period
                                sch_model.Add(covers == 1)
                            elif not can_be_before:
                                # start is always >= window_lo; covers ↔ start ≤ window_hi
                                sch_model.Add(start_var <= window_hi).OnlyEnforceIf(covers)
                                sch_model.Add(start_var > window_hi).OnlyEnforceIf(covers.Not())
                            elif not can_be_after:
                                # start is always ≤ window_hi; covers ↔ start >= window_lo
                                sch_model.Add(start_var >= window_lo).OnlyEnforceIf(covers)
                                sch_model.Add(start_var < window_lo).OnlyEnforceIf(covers.Not())
                            else:
                                # Two-sided: covers ↔ start ∈ [window_lo, window_hi]
                                sch_model.Add(start_var >= window_lo).OnlyEnforceIf(covers)
                                sch_model.Add(start_var <= window_hi).OnlyEnforceIf(covers)

                                out_lo = sch_model.NewBoolVar(f"ol_{s}_{d}_{i}_{b_name}_{p}")
                                sch_model.Add(start_var < window_lo).OnlyEnforceIf(out_lo)
                                sch_model.Add(start_var >= window_lo).OnlyEnforceIf(out_lo.Not())

                                out_hi = sch_model.NewBoolVar(f"oh_{s}_{d}_{i}_{b_name}_{p}")
                                sch_model.Add(start_var > window_hi).OnlyEnforceIf(out_hi)
                                sch_model.Add(start_var <= window_hi).OnlyEnforceIf(out_hi.Not())

                                # NOT covers → out_lo OR out_hi
                                sch_model.AddBoolOr([covers, out_lo, out_hi])
                                sch_model.AddImplication(covers, out_lo.Not())
                                sch_model.AddImplication(covers, out_hi.Not())

                            covers_vars.append(covers)

                if covers_vars:
                    sch_model.Add(sum(covers_vars) <= slack)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_search_time
        solver.num_search_workers = self.num_search_workers

        status = solver.Solve(sch_model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            break_schedule = []
            for (s, d, i, b_name), start_var in start_vars.items():
                dur = break_by_name[b_name]["duration_periods"]
                start_val = solver.Value(start_var)
                break_schedule.append({
                    "shift": s,
                    "day": d,
                    "slot": i,
                    "break_name": b_name,
                    "start_period": start_val,
                    "end_period": start_val + dur,
                })

            self.solution_ = {
                "status": solver.StatusName(status),
                "cost": solver.ObjectiveValue(),
                "break_schedule": break_schedule,
            }
        else:
            self.solution_ = {
                "status": solver.StatusName(status),
                "cost": -1,
                "break_schedule": [
                    {
                        "shift": "Unknown",
                        "day": -1,
                        "slot": -1,
                        "break_name": "Unknown",
                        "start_period": -1,
                        "end_period": -1,
                    }
                ],
            }

        return self.solution_
