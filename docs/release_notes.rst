Release Notes
=============

Some notes on new features in various releases

What's new in 0.5.2
-------------------

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* Add support for Python 3.12, 3.13, and 3.14.
* Update GitHub Actions tests on all supported Python versions.
* Update project dependencies to versions compatible with modern Python and NumPy releases.
* Update :class:`~pyworkforce.utils.ParameterGrid` to work with NumPy 2.x.
* Validate Erlang C systems with zero productive positions or traffic intensity greater than or equal to positions.
* Validate :meth:`~pyworkforce.queuing.ErlangC.required_positions` with ``max_occupancy > 0``.
* Fix the :class:`~pyworkforce.queuing.MultiErlangC` inconsistent-results error message to report the expected
  number of scenario combinations.

What's new in 0.5.1
-------------------

^^^^^^^^^
Features:
^^^^^^^^^

* Remove support for Python 3.7 and add support for Python up to 3.11.
* Update the project dependencies

What's new in 0.5.0
-------------------

^^^^^^^^^
Features:
^^^^^^^^^

* Added a new type of solver under the class :class:`~pyworkforce.rostering.MinHoursRoster`
  for rostering problems, it can find the roster of resources for each day
  and shift subject to shift restrictions, resting days, shifts preferences, bans, and more.

* Added the properties ``waiting_probability_params``, ``service_level_params``, ``achieved_occupancy_params``,
  and ``required_positions_params`` in :class:`~pyworkforce.queuing.MultiErlangC` to track in which
  combination order each method returns a solution.

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* The misspelled ``queing`` module was renamed to ``queuing``.
* The ``shifts`` module was renamed to ``scheduling``.

What's new in 0.4.1 and below
------------------------------

* Implemented :class:`~pyworkforce.queuing.ErlangC` for solving queue systems positions requirements

* Implemented :class:`~pyworkforce.queuing.MultiErlangC` as a parallel implementation for multi-input
  `ErlangC`, similar to scikit-learn's param_grid in Grid Search

* Added :class:`~pyworkforce.scheduling.MinAbsDifference` and :class:`~pyworkforce.scheduling.MinRequiredResources`
  solvers to find the optimal number of resources to allocate in a shift,
  based on a pre-defined requirement of the number of resources per period of the day.

* GitHub Actions for pytest and Codecov reports

* Examples and tutorials on all the package features

* Initial docs setup
