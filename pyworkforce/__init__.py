from ._version import __version__
from .queuing import ErlangA, ErlangC, MultiErlangC
from .rostering import MinHoursRoster
from .scheduling import MinAbsDifference, MinRequiredResources

__all__ = [
    "ErlangC",
    "ErlangA",
    "MultiErlangC",
    "MinRequiredResources",
    "MinAbsDifference",
    "MinHoursRoster",
    "__version__",
]
