"""Check API selection independently of the installed OR-Tools version."""

import os

import pytest
from ortools.sat.python import cp_model

from pyworkforce.utils._cp_sat import method, objective_value


def test_modern_method_does_not_access_legacy_alias():
    class SupportsBoth:
        def add(self, value):
            return value

        @property
        def Add(self):
            raise AssertionError("The deprecated alias must not be accessed")

    assert method(SupportsBoth(), "add")(7) == 7


def test_legacy_method_and_negation_are_resolved():
    class Legacy:
        def Add(self, value):
            return value

        def Not(self):
            return "negated literal"

    assert method(Legacy(), "add")(9) == 9
    assert method(Legacy(), "negated")() == "negated literal"


def test_objective_value_handles_old_method_and_new_property():
    class Modern:
        @property
        def objective_value(self):
            return 0.0

        def ObjectiveValue(self):
            raise AssertionError("Do not fall back for a zero objective")

    class Legacy:
        def ObjectiveValue(self):
            return 9.0

    assert objective_value(Modern()) == 0.0
    assert objective_value(Legacy()) == 9.0


@pytest.mark.skipif(
    os.environ.get("PYWORKFORCE_TEST_CP_SAT_DEPRECATIONS") != "1",
    reason="positive control is specific to the OR-Tools 10 release candidate",
)
def test_rc_warns_on_a_legacy_cp_sat_method():
    with pytest.warns(DeprecationWarning, match=r"NewIntVar is a deprecated function\."):
        cp_model.CpModel().NewIntVar(0, 1, "warning_control")
