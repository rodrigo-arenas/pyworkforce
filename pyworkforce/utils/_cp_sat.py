"""Private bridge between legacy and current OR-Tools CP-SAT APIs."""

from collections.abc import Callable


def method(obj: object, name: str) -> Callable:
    """Resolve a method, using CamelCase only on older OR-Tools versions."""
    modern = getattr(obj, name, None)
    if modern is not None:
        return modern
    legacy = "Not" if name == "negated" else "".join(part.title() for part in name.split("_"))
    return getattr(obj, legacy)


def objective_value(solver) -> float:
    """Read the newer property without invoking the deprecated method."""
    if getattr(type(solver), "objective_value", None) is not None:
        return solver.objective_value
    return solver.ObjectiveValue()


def add_enforced(model, condition, literal) -> None:
    """Add a constraint that is active when its Boolean literal is true."""
    constraint = method(model, "add")(condition)
    method(constraint, "only_enforce_if")(literal)
