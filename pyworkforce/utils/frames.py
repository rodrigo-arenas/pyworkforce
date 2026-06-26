"""Helpers to turn solver results into tidy :class:`pandas.DataFrame` objects."""


def results_to_dataframe(results, params=None):
    """Combine grid results (and the parameters that produced them) into a frame.

    This is a convenience for the ``Multi*`` estimators: their methods return a
    list of result dictionaries, and the matching ``*_params`` attribute holds
    the parallel list of ``(estimator_params, method_params)`` tuples. Passing
    both yields a single table with one row per scenario.

    Parameters
    ----------
    results : list
        The list returned by a ``Multi*`` method. Each element may be a
        dictionary (e.g. ``required_positions``) or a scalar (e.g.
        ``service_level``); scalars are placed in a ``result`` column.
    params : list, optional
        The matching ``*_params`` list of ``(estimator_params, method_params)``
        tuples. When provided, those parameters become leading columns.

    Returns
    -------
    pandas.DataFrame
        One row per scenario, with parameter columns first (when ``params`` is
        given) followed by the result columns. When a result key collides with
        a parameter name (for example ``service_level`` is both a target input
        and an achieved output of ``required_positions``), the result column is
        suffixed with ``_result`` so both values are preserved.

    Examples
    --------
    >>> from pyworkforce.queuing import MultiErlangC
    >>> from pyworkforce.utils import results_to_dataframe
    >>> grid = {"transactions": [100], "aht": [3], "interval": [30],
    ...         "asa": [20 / 60], "shrinkage": [0.3]}
    >>> multi = MultiErlangC(param_grid=grid, n_jobs=1)
    >>> results = multi.required_positions({"service_level": [0.8, 0.9]})
    >>> df = results_to_dataframe(results, multi.required_positions_params)
    >>> sorted(df.columns)[:3]
    ['aht', 'asa', 'interval']
    """
    import pandas as pd

    rows = []
    if params is not None and len(params) != len(results):
        raise ValueError(
            f"results and params must have the same length, "
            f"got {len(results)} and {len(params)}")

    for index, result in enumerate(results):
        row = {}
        if params is not None:
            estimator_params, method_params = params[index]
            row.update(estimator_params)
            row.update(method_params)
        if isinstance(result, dict):
            for key, value in result.items():
                # Preserve input parameters that share a name with a result key.
                column = f"{key}_result" if key in row else key
                row[column] = value
        else:
            row["result"] = result
        rows.append(row)

    return pd.DataFrame(rows)
