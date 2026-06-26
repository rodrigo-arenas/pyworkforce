"""Multi-skill staffing: find the minimum-cost agent mix across skill profiles.

In a real contact centre, agents typically carry multiple skills (e.g. English,
Spanish, Billing, Technical).  A call of type *k* can be handled by *any* agent
who holds skill *k*.  Given per-skill staffing requirements — normally the
output of :class:`~pyworkforce.queuing.ErlangC` or
:class:`~pyworkforce.queuing.ErlangA` — this module solves the integer programme
that minimises the total (optionally weighted) headcount while ensuring every
skill's coverage is met.

The result integrates with the scheduling and rostering steps: the *agents per
profile* figures feed directly into the per-shift scheduling problem.
"""

from ortools.sat.python import cp_model

from pyworkforce.base import BaseWorkforce
from pyworkforce.utils.validation import check_positive_float, check_positive_integer


class MultiSkillStaffing(BaseWorkforce):
    """
    Minimum-cost agent-mix optimiser for multi-skill contact-centre staffing.

    Solves the integer programme::

        minimise   Σ_s  cost[s] · n[s]
        subject to Σ_{s : k ∈ profile(s)} n[s] ≥ required[k]   ∀ k ∈ skills
                   n[s] ≥ 0,  integer                            ∀ s

    This is the correct model when a flexible agent (one who holds *both* skills
    A and B) counts equally towards the coverage of *both* A and *B*.

    Parameters
    ----------
    skills : list[str]
        Names of the distinct skill types that must be staffed
        (e.g. ``["English", "Billing", "Technical"]``).
    profiles : list[dict]
        Each element describes one agent skill-profile::

            {
                "name":   str,        # unique identifier
                "skills": list[str],  # skills this profile covers (subset of *skills*)
                "cost":   float,      # optional cost per agent; default 1.0
            }

        Every skill in *skills* must be covered by at least one profile,
        otherwise the problem is trivially infeasible.
    required_positions : dict
        ``{"skill_name": n}`` — minimum agents needed for each skill.  Pass
        ``result["raw_positions"]`` from :class:`~pyworkforce.queuing.ErlangC`
        or :class:`~pyworkforce.queuing.ErlangA` here.  Keys must match *skills*
        exactly.
    max_agents : int, optional
        Hard cap on the total number of agents across all profiles.  Omit for
        an unconstrained search.
    max_search_time : float, default 60.0
        Maximum solver wall-clock time in seconds.
    num_search_workers : int, default 2
        Number of parallel search workers.

    Attributes
    ----------
    solution_ : dict or None
        Populated by :meth:`solve`.

    Examples
    --------
    >>> from pyworkforce.staffing import MultiSkillStaffing
    >>> skills = ["Billing", "Technical"]
    >>> profiles = [
    ...     {"name": "Billing_only",   "skills": ["Billing"],             "cost": 1.0},
    ...     {"name": "Technical_only", "skills": ["Technical"],           "cost": 1.0},
    ...     {"name": "Flexible",       "skills": ["Billing", "Technical"],"cost": 1.5},
    ... ]
    >>> required = {"Billing": 5, "Technical": 3}
    >>> ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    >>> result = ms.solve()
    >>> result["status"]
    'OPTIMAL'
    >>> result["total_agents"]
    5
    """

    def __init__(
        self,
        skills: list,
        profiles: list,
        required_positions: dict,
        max_agents: int = None,
        max_search_time: float = 60.0,
        num_search_workers: int = 2,
    ):
        check_positive_float("max_search_time", max_search_time)
        check_positive_integer("num_search_workers", num_search_workers)

        if not skills:
            raise ValueError("skills must be a non-empty list")
        if len(skills) != len(set(skills)):
            raise ValueError("skills must be unique")

        if not profiles:
            raise ValueError("profiles must be a non-empty list")

        profile_names = [p.get("name") for p in profiles]
        if any(n is None for n in profile_names):
            raise ValueError("every profile must have a 'name' key")
        if len(profile_names) != len(set(profile_names)):
            raise ValueError("profile names must be unique")

        skill_set = set(skills)
        for p in profiles:
            if "skills" not in p:
                raise ValueError(f"profile '{p['name']}' is missing the 'skills' key")
            unknown = set(p["skills"]) - skill_set
            if unknown:
                raise ValueError(
                    f"profile '{p['name']}' references unknown skills: {sorted(unknown)}"
                )

        missing_req = skill_set - set(required_positions)
        if missing_req:
            raise ValueError(
                f"required_positions is missing keys for skills: {sorted(missing_req)}"
            )
        extra_req = set(required_positions) - skill_set
        if extra_req:
            raise ValueError(
                f"required_positions contains unknown skills: {sorted(extra_req)}"
            )
        for skill, n in required_positions.items():
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                raise ValueError(
                    f"required_positions['{skill}'] must be a non-negative integer, got {n!r}"
                )

        uncovered = {
            sk for sk in skills
            if not any(sk in p["skills"] for p in profiles)
        }
        if uncovered:
            raise ValueError(
                f"No profile covers skill(s): {sorted(uncovered)}. "
                "The problem would be infeasible for any required count > 0."
            )

        if max_agents is not None:
            check_positive_integer("max_agents", max_agents)

        self.skills = skills
        self.profiles = profiles
        self.required_positions = required_positions
        self.max_agents = max_agents
        self.max_search_time = max_search_time
        self.num_search_workers = num_search_workers
        self.solution_ = None

    def solve(self) -> dict:
        """
        Run the CP-SAT integer programme.

        Returns
        -------
        dict
            ``status``
                Solver status string (``"OPTIMAL"``, ``"FEASIBLE"``, or
                ``"INFEASIBLE"``).
            ``cost``
                Achieved objective value (weighted headcount), or −1 when
                infeasible.
            ``total_agents``
                Sum of agents across all profiles, or −1 when infeasible.
            ``agents_per_profile``
                List of ``{"profile": name, "agents": n}`` dicts.
            ``skill_coverage``
                ``{"skill": n}`` — total agents covering each skill in the
                solution.  Useful for verifying that all requirements are met.
        """
        sch_model = cp_model.CpModel()

        # Variable upper bound: no profile can ever need more than the sum of
        # all requirements (worst-case one profile serves every skill type).
        ub = max(1, sum(self.required_positions.values()))
        if self.max_agents is not None:
            ub = min(ub, self.max_agents)

        n_agents = {
            p["name"]: sch_model.NewIntVar(0, ub, f"n_{p['name']}")
            for p in self.profiles
        }

        # Coverage constraints
        for skill in self.skills:
            req = self.required_positions[skill]
            if req == 0:
                continue
            contributors = [
                n_agents[p["name"]]
                for p in self.profiles
                if skill in p["skills"]
            ]
            sch_model.Add(sum(contributors) >= req)

        # Optional total-agent cap
        if self.max_agents is not None:
            sch_model.Add(sum(n_agents.values()) <= self.max_agents)

        # Objective: minimise weighted headcount
        sch_model.Minimize(
            sum(p.get("cost", 1.0) * n_agents[p["name"]] for p in self.profiles)
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_search_time
        solver.num_search_workers = self.num_search_workers

        status = solver.Solve(sch_model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            agents_per_profile = [
                {"profile": p["name"], "agents": solver.Value(n_agents[p["name"]])}
                for p in self.profiles
            ]
            total_agents = sum(e["agents"] for e in agents_per_profile)

            skill_coverage = {}
            for skill in self.skills:
                skill_coverage[skill] = sum(
                    solver.Value(n_agents[p["name"]])
                    for p in self.profiles
                    if skill in p["skills"]
                )

            self.solution_ = {
                "status": solver.StatusName(status),
                "cost": solver.ObjectiveValue(),
                "total_agents": total_agents,
                "agents_per_profile": agents_per_profile,
                "skill_coverage": skill_coverage,
            }
        else:
            self.solution_ = {
                "status": solver.StatusName(status),
                "cost": -1,
                "total_agents": -1,
                "agents_per_profile": [{"profile": "Unknown", "agents": -1}],
                "skill_coverage": {skill: -1 for skill in self.skills},
            }

        return self.solution_
