from ._version import __version__
from .breaks import BreakScheduler
from .queuing import ErlangA, ErlangB, ErlangC, MultiErlangA, MultiErlangB, MultiErlangC
from .rostering import MinHoursRoster
from .scheduling import MinAbsDifference, MinRequiredResources
from .staffing import MultiSkillStaffing

__all__ = [
    "ErlangC",
    "ErlangA",
    "ErlangB",
    "MultiErlangC",
    "MultiErlangA",
    "MultiErlangB",
    "MinRequiredResources",
    "MinAbsDifference",
    "MinHoursRoster",
    "BreakScheduler",
    "MultiSkillStaffing",
    "__version__",
]
