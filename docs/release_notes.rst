Release Notes
=============

Some notes on new features in various releases

What's new in 0.5.0dev0
-----------------------

^^^^^^^^^
Features:
^^^^^^^^^

* Added a new type of solver under the class :class:`~pyworkforce.rostering.MinHoursRoster`
  for rostering problems, it can find the roster of resources for each day
  and shift subject to shift restrictions, resting days, shifts preferences, bans, and more.

* Added the properties `waiting_probability_params`, `service_level_params`, `achieved_occupancy_params`,
  and `required_positions_params` in :class:`~pyworkforce.shifts.MultiErlangC` to track in which
  combination order each method returns a solution.

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* The queing module was renamed to queuing
* The shifts module was renamed to scheduling

What's new in 0.4.1 and bellow
------------------------------

* Implemented :class:`~pyworkforce.queuing.ErlangC` for solving queue systems positions requirements

* Implemented :class:`~pyworkforce.queuing.MultiErlangC` as a parallel implementation for multi-input
  `ErlangC`, similar to scikit-learn's param_grid in Grid Search

* Added :class:`~pyworkforce.scheduling.MinAbsDifference` and :class:`~pyworkforce.scheduling.MinRequiredResources`
  solvers to find the optimal number of resources to allocate in a shift,
  based on a pre-defined requirement of the number of resources per period of the day.

* Github actions for pytest and Codecov report

* Examples and tutorials on all the package features

* Initial docs setup
