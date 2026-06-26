"""Helpers to build and inspect ``shifts_coverage`` definitions.

The scheduling solvers expect ``shifts_coverage`` as a dictionary mapping a
shift name to a 0/1 array of length ``periods`` (1 when the shift covers that
period). Writing those arrays by hand is tedious and error prone, so this
module provides small, deterministic builders to create them from more natural
descriptions: explicit period indices, ``(start, length)`` spans or clock
hours.
"""

from pyworkforce.utils.validation import check_positive_integer

__all__ = [
    "shift_coverage_from_periods",
    "shift_coverage_from_spans",
    "shift_coverage_from_hours",
    "validate_shift_coverage",
    "coverage_to_dataframe",
]


def _empty_row(num_periods):
    return [0] * num_periods


def shift_coverage_from_periods(periods_by_shift, num_periods):
    """Build a coverage dictionary from explicit period indices.

    Parameters
    ----------
    periods_by_shift : dict
        Mapping ``{shift_name: iterable_of_period_indices}``. Indices are
        zero-based and must be in ``range(num_periods)``.
    num_periods : int
        Number of periods in a day (the length of every coverage array).

    Returns
    -------
    dict
        Mapping ``{shift_name: [0/1, ...]}`` with arrays of length
        ``num_periods``.

    Examples
    --------
    >>> shift_coverage_from_periods({"Morning": [0, 1, 2]}, num_periods=4)
    {'Morning': [1, 1, 1, 0]}
    """
    check_positive_integer("num_periods", num_periods)
    if not isinstance(periods_by_shift, dict) or not periods_by_shift:
        raise ValueError("periods_by_shift must be a non-empty dictionary")

    coverage = {}
    for shift_name, periods in periods_by_shift.items():
        row = _empty_row(num_periods)
        for period in periods:
            if not isinstance(period, int) or isinstance(period, bool):
                raise ValueError(
                    f"shift '{shift_name}' has a non-integer period index: {period!r}")
            if not 0 <= period < num_periods:
                raise ValueError(
                    f"shift '{shift_name}' has period index {period} outside "
                    f"range [0, {num_periods})")
            row[period] = 1
        coverage[shift_name] = row
    return coverage


def shift_coverage_from_spans(spans_by_shift, num_periods, wrap_around=True):
    """Build a coverage dictionary from ``(start, length)`` spans.

    Parameters
    ----------
    spans_by_shift : dict
        Mapping ``{shift_name: (start_period, length)}`` or
        ``{shift_name: [(start, length), ...]}`` for shifts split into several
        blocks. ``start`` is a zero-based period index and ``length`` is the
        number of consecutive periods covered.
    num_periods : int
        Number of periods in a day.
    wrap_around : bool, default=True
        If True, spans that extend past the end of the day continue from
        period 0 (useful for overnight shifts). If False, such spans raise a
        ``ValueError``.

    Returns
    -------
    dict
        Mapping ``{shift_name: [0/1, ...]}`` with arrays of length
        ``num_periods``.

    Examples
    --------
    >>> shift_coverage_from_spans({"Night": (3, 2)}, num_periods=4)
    {'Night': [0, 0, 0, 1]}
    >>> shift_coverage_from_spans({"Night": (3, 3)}, num_periods=4)
    {'Night': [1, 1, 0, 1]}
    """
    check_positive_integer("num_periods", num_periods)
    if not isinstance(spans_by_shift, dict) or not spans_by_shift:
        raise ValueError("spans_by_shift must be a non-empty dictionary")

    coverage = {}
    for shift_name, spans in spans_by_shift.items():
        # Allow a single (start, length) tuple or a list of them.
        if len(spans) == 2 and all(isinstance(v, int) and not isinstance(v, bool) for v in spans):
            spans = [spans]

        row = _empty_row(num_periods)
        for span in spans:
            start, length = span
            check_positive_integer("span length", length)
            if not isinstance(start, int) or isinstance(start, bool):
                raise ValueError(
                    f"shift '{shift_name}' has a non-integer start: {start!r}")
            if not 0 <= start < num_periods:
                raise ValueError(
                    f"shift '{shift_name}' has start {start} outside range "
                    f"[0, {num_periods})")
            if not wrap_around and start + length > num_periods:
                raise ValueError(
                    f"shift '{shift_name}' span ({start}, {length}) extends past "
                    f"the end of the day and wrap_around is False")
            for offset in range(length):
                row[(start + offset) % num_periods] = 1
        coverage[shift_name] = row
    return coverage


def shift_coverage_from_hours(hours_by_shift, num_periods=24, period_minutes=60,
                              wrap_around=True):
    """Build a coverage dictionary from ``(start_hour, end_hour)`` clock times.

    Hours are interpreted on a 24-hour clock. A period is marked as covered
    when its start time falls inside the ``[start_hour, end_hour)`` window, so
    windows should align with the period grid (e.g. half-integer hours for
    30-minute periods).

    Parameters
    ----------
    hours_by_shift : dict
        Mapping ``{shift_name: (start_hour, end_hour)}`` with hours as numbers
        in ``[0, 24]``. ``end_hour`` may be smaller than ``start_hour`` for
        overnight shifts (e.g. ``(22, 6)``).
    num_periods : int, default=24
        Number of periods in a day. ``num_periods * period_minutes`` must equal
        ``1440`` (a full day).
    period_minutes : int, default=60
        Length of each period in minutes.
    wrap_around : bool, default=True
        Whether overnight windows (``end_hour <= start_hour``) are allowed.

    Returns
    -------
    dict
        Mapping ``{shift_name: [0/1, ...]}`` with arrays of length
        ``num_periods``.

    Examples
    --------
    >>> cov = shift_coverage_from_hours({"Day": (8, 12)}, num_periods=24)
    >>> sum(cov["Day"])
    4
    """
    check_positive_integer("num_periods", num_periods)
    check_positive_integer("period_minutes", period_minutes)
    if num_periods * period_minutes != 24 * 60:
        raise ValueError(
            f"num_periods * period_minutes must equal {24 * 60} (a full day), "
            f"got {num_periods * period_minutes}")
    if not isinstance(hours_by_shift, dict) or not hours_by_shift:
        raise ValueError("hours_by_shift must be a non-empty dictionary")

    periods_per_hour = 60 / period_minutes
    spans = {}
    for shift_name, window in hours_by_shift.items():
        start_hour, end_hour = window
        for label, value in (("start_hour", start_hour), ("end_hour", end_hour)):
            if not 0 <= value <= 24:
                raise ValueError(
                    f"shift '{shift_name}' {label} must be in [0, 24], got {value}")

        start_period = start_hour * periods_per_hour
        end_period = end_hour * periods_per_hour
        for label, value in (("start_hour", start_period), ("end_hour", end_period)):
            if abs(value - round(value)) > 1e-9:
                raise ValueError(
                    f"shift '{shift_name}' {label} does not align with a "
                    f"{period_minutes}-minute period grid")
        start_period = int(round(start_period))
        end_period = int(round(end_period))

        if end_period > start_period:
            length = end_period - start_period
        elif wrap_around:
            length = (num_periods - start_period) + end_period
        else:
            raise ValueError(
                f"shift '{shift_name}' is an overnight window {window} but "
                f"wrap_around is False")
        if length == 0:
            raise ValueError(f"shift '{shift_name}' covers zero periods")
        spans[shift_name] = (start_period % num_periods, length)

    return shift_coverage_from_spans(spans, num_periods, wrap_around=wrap_around)


def validate_shift_coverage(shifts_coverage, num_periods=None):
    """Validate a ``shifts_coverage`` dictionary.

    Parameters
    ----------
    shifts_coverage : dict
        Mapping ``{shift_name: array}`` to validate.
    num_periods : int, optional
        Expected length of each coverage array. If omitted, the length of the
        first array is used as the reference.

    Returns
    -------
    int
        The (validated) number of periods.

    Raises
    ------
    ValueError
        If the dictionary is empty, arrays have inconsistent lengths, or any
        value is not 0/1.
    """
    if not isinstance(shifts_coverage, dict) or not shifts_coverage:
        raise ValueError("shifts_coverage must be a non-empty dictionary")

    reference = num_periods
    for shift_name, coverage in shifts_coverage.items():
        if reference is None:
            reference = len(coverage)
        if len(coverage) != reference:
            raise ValueError(
                f"shift '{shift_name}' has length {len(coverage)}, expected {reference}")
        for value in coverage:
            if value not in (0, 1):
                raise ValueError(
                    f"shift '{shift_name}' contains a non-binary value: {value!r}")
    return reference


def coverage_to_dataframe(shifts_coverage):
    """Return a ``pandas.DataFrame`` view of a coverage dictionary.

    Rows are shift names and columns are period indices, which makes coverage
    easy to print or inspect in notebooks.

    Parameters
    ----------
    shifts_coverage : dict
        Mapping ``{shift_name: array}``.

    Returns
    -------
    pandas.DataFrame
    """
    import pandas as pd

    validate_shift_coverage(shifts_coverage)
    return pd.DataFrame.from_dict(shifts_coverage, orient="index")
