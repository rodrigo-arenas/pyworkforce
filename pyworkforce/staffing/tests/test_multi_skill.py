import pytest

from pyworkforce.staffing import MultiSkillStaffing

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coverage(result, profiles):
    """Return {skill: total_agents_covering_it} from a solved result."""
    return result["skill_coverage"]


def _agents_by_profile(result):
    return {e["profile"]: e["agents"] for e in result["agents_per_profile"]}


# ---------------------------------------------------------------------------
# Happy-path / optimality tests
# ---------------------------------------------------------------------------

def test_two_skills_known_optimal():
    """3 flexible + 2 billing-only minimises cost to 6.5 (vs 8.0 for pure dedicated)."""
    skills = ["Billing", "Technical"]
    profiles = [
        {"name": "Billing_only",   "skills": ["Billing"],              "cost": 1.0},
        {"name": "Technical_only", "skills": ["Technical"],            "cost": 1.0},
        {"name": "Flexible",       "skills": ["Billing", "Technical"], "cost": 1.5},
    ]
    required = {"Billing": 5, "Technical": 3}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] == "OPTIMAL"
    assert result["total_agents"] == 5
    assert result["cost"] == pytest.approx(6.5)

    # Coverage must meet requirements
    assert result["skill_coverage"]["Billing"] >= 5
    assert result["skill_coverage"]["Technical"] >= 3

    # Only valid because flexible costs 1.5 and each dedicated costs 1.0
    # Optimal is 3 flexible + 2 billing_only
    ap = _agents_by_profile(result)
    assert ap["Flexible"] == 3
    assert ap["Billing_only"] == 2
    assert ap["Technical_only"] == 0


def test_dedicated_optimal_when_flexible_is_expensive():
    """When flexible cost > sum of dedicated costs it covers, use dedicated agents."""
    skills = ["A", "B"]
    profiles = [
        {"name": "A_only", "skills": ["A"], "cost": 1.0},
        {"name": "B_only", "skills": ["B"], "cost": 1.0},
        {"name": "Flex",   "skills": ["A", "B"], "cost": 3.0},
    ]
    required = {"A": 4, "B": 2}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] == "OPTIMAL"
    # Optimal: 4 A-only + 2 B-only = cost 6.0
    # Alternative: 4 Flex = cost 12.0 → dedicated wins
    assert result["cost"] == pytest.approx(6.0)
    ap = _agents_by_profile(result)
    assert ap["Flex"] == 0


def test_single_skill_returns_required():
    skills = ["English"]
    profiles = [{"name": "English", "skills": ["English"]}]
    required = {"English": 7}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] == "OPTIMAL"
    assert result["total_agents"] == 7
    assert result["skill_coverage"]["English"] >= 7


def test_three_skills_dedicated_only():
    skills = ["A", "B", "C"]
    profiles = [
        {"name": "A", "skills": ["A"]},
        {"name": "B", "skills": ["B"]},
        {"name": "C", "skills": ["C"]},
    ]
    required = {"A": 4, "B": 2, "C": 3}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] == "OPTIMAL"
    assert result["total_agents"] == 9
    assert result["cost"] == pytest.approx(9.0)


def test_zero_required_for_one_skill():
    """A skill with required=0 is always satisfied; no agents needed for it."""
    skills = ["A", "B"]
    profiles = [
        {"name": "A_only", "skills": ["A"]},
        {"name": "B_only", "skills": ["B"]},
    ]
    required = {"A": 5, "B": 0}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] == "OPTIMAL"
    assert result["total_agents"] == 5
    ap = _agents_by_profile(result)
    assert ap["B_only"] == 0


def test_solution_stored_on_instance():
    ms = MultiSkillStaffing(
        skills=["X"],
        profiles=[{"name": "X", "skills": ["X"]}],
        required_positions={"X": 3},
    )
    result = ms.solve()
    assert ms.solution_ is result


def test_skill_coverage_field_satisfies_requirements():
    """skill_coverage in the output must be >= required for every skill."""
    skills = ["P", "Q", "R"]
    profiles = [
        {"name": "PQ", "skills": ["P", "Q"], "cost": 1.2},
        {"name": "QR", "skills": ["Q", "R"], "cost": 1.2},
        {"name": "P",  "skills": ["P"],       "cost": 1.0},
        {"name": "R",  "skills": ["R"],       "cost": 1.0},
    ]
    required = {"P": 4, "Q": 3, "R": 5}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    for skill, req in required.items():
        assert result["skill_coverage"][skill] >= req, (
            f"Coverage for '{skill}' is {result['skill_coverage'][skill]}, need {req}"
        )


def test_default_cost_is_one():
    """Profiles without a 'cost' key should default to 1.0."""
    skills = ["A"]
    profiles = [{"name": "A", "skills": ["A"]}]  # no "cost" key
    required = {"A": 3}

    ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
    result = ms.solve()

    assert result["cost"] == pytest.approx(3.0)


def test_get_params():
    ms = MultiSkillStaffing(
        skills=["A"],
        profiles=[{"name": "A", "skills": ["A"]}],
        required_positions={"A": 2},
        max_agents=10,
    )
    p = ms.get_params()
    assert p["skills"] == ["A"]
    assert p["max_agents"] == 10
    assert p["max_search_time"] == 60.0


# ---------------------------------------------------------------------------
# Infeasible tests
# ---------------------------------------------------------------------------

def test_infeasible_max_agents_too_small():
    """Minimum 5 agents needed; cap at 4 must trigger INFEASIBLE."""
    skills = ["A", "B"]
    profiles = [
        {"name": "Flex", "skills": ["A", "B"]},
    ]
    required = {"A": 5, "B": 3}

    ms = MultiSkillStaffing(
        skills=skills, profiles=profiles,
        required_positions=required, max_agents=4,
    )
    result = ms.solve()

    assert result["status"] == "INFEASIBLE"
    assert result["cost"] == -1
    assert result["total_agents"] == -1


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_empty_skills_raises():
    with pytest.raises(ValueError, match="skills must be a non-empty"):
        MultiSkillStaffing(
            skills=[], profiles=[{"name": "X", "skills": []}],
            required_positions={},
        )


def test_duplicate_skills_raises():
    with pytest.raises(ValueError, match="unique"):
        MultiSkillStaffing(
            skills=["A", "A"],
            profiles=[{"name": "X", "skills": ["A"]}],
            required_positions={"A": 1, "A": 1},  # noqa: F601
        )


def test_duplicate_profile_names_raises():
    with pytest.raises(ValueError, match="profile names must be unique"):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[
                {"name": "X", "skills": ["A"]},
                {"name": "X", "skills": ["A"]},
            ],
            required_positions={"A": 1},
        )


def test_profile_references_unknown_skill_raises():
    with pytest.raises(ValueError, match="unknown skills"):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[{"name": "P", "skills": ["A", "Z"]}],
            required_positions={"A": 1},
        )


def test_required_positions_missing_key_raises():
    with pytest.raises(ValueError, match="missing keys"):
        MultiSkillStaffing(
            skills=["A", "B"],
            profiles=[{"name": "AB", "skills": ["A", "B"]}],
            required_positions={"A": 1},  # missing "B"
        )


def test_required_positions_extra_key_raises():
    with pytest.raises(ValueError, match="unknown skills"):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[{"name": "A", "skills": ["A"]}],
            required_positions={"A": 1, "Z": 2},
        )


def test_required_positions_negative_raises():
    with pytest.raises(ValueError, match="non-negative integer"):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[{"name": "A", "skills": ["A"]}],
            required_positions={"A": -1},
        )


def test_uncovered_skill_raises():
    with pytest.raises(ValueError, match="No profile covers"):
        MultiSkillStaffing(
            skills=["A", "B"],
            profiles=[{"name": "A_only", "skills": ["A"]}],
            required_positions={"A": 1, "B": 1},
        )


def test_profile_missing_skills_key_raises():
    with pytest.raises(ValueError, match="missing the 'skills' key"):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[{"name": "P"}],  # no "skills"
            required_positions={"A": 1},
        )


def test_invalid_max_agents_raises():
    with pytest.raises(ValueError):
        MultiSkillStaffing(
            skills=["A"],
            profiles=[{"name": "A", "skills": ["A"]}],
            required_positions={"A": 1},
            max_agents=0,
        )
