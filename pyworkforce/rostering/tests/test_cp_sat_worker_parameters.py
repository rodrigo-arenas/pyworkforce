import pytest
from ortools.sat.python import cp_model

from pyworkforce.breaks import BreakScheduler
from pyworkforce.rostering.tests.test_validation import make
from pyworkforce.staffing import MultiSkillStaffing


@pytest.mark.parametrize(
    "build_solver",
    [
        lambda: make(num_search_workers=3),
        lambda: BreakScheduler(
            num_days=1,
            periods=8,
            shifts_coverage={"Morning": [1] * 8},
            scheduled_resources={"Morning": [4]},
            breaks=[
                {
                    "name": "Short",
                    "duration_periods": 1,
                    "min_start_after": 1,
                    "max_end_before": 1,
                }
            ],
            min_coverage=[[3] * 8],
            num_search_workers=3,
        ),
        lambda: MultiSkillStaffing(
            skills=["Billing"],
            profiles=[{"name": "Billing", "skills": ["Billing"], "cost": 1}],
            required_positions={"Billing": 2},
            num_search_workers=3,
        ),
    ],
    ids=["roster", "breaks", "staffing"],
)
def test_worker_count_reaches_cp_sat(monkeypatch, build_solver):
    """Check the parameter handed to CP-SAT, not its execution time."""
    solver_class = cp_model.CpSolver
    solve_name = "solve" if hasattr(solver_class, "solve") else "Solve"
    real_solve = getattr(solver_class, solve_name)
    observed = []

    def capture(solver, *args, **kwargs):
        observed.append(solver.parameters.num_search_workers)
        return real_solve(solver, *args, **kwargs)

    monkeypatch.setattr(solver_class, solve_name, capture)
    assert build_solver().solve()["status"] == "OPTIMAL"
    assert observed == [3]

