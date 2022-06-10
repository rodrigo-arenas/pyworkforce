Release Notes
=============

Some notes on new features in various releases

What's new in 0.5.0dev0
-----------------------

^^^^^^^^^
Features:
^^^^^^^^^

* Added the properties `waiting_probability_params`, `service_level_params`, `achieved_occupancy_params`,
  and `required_positions_params` in :class:`~pyworkforce.shifts.MultiErlangC` to track in which
  combination order each method returns a solution.

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* The queing module was rename to queuing

What's new in 0.4.1 and bellow
------------------------------

* Implemented :class:`~pyworkforce.queuing.ErlangC` for solving queue systems positions requirements

* Implemented :class:`~pyworkforce.queuing.MultiErlangC` as a parallel implementation for multi-input
  `ErlangC`, similar to scikit-learn's param_grid in Grid Search

* Added :class:`~pyworkforce.shifts.MinAbsDifference` and :class:`~pyworkforce.shifts.MinRequiredResources`
  solvers to find the optimal number of resources to allocate in a shift,
  based on a pre-defined requirement of the number of resources per period of the day.

* Github actions for pytest and Codecov report

* Examples and tutorials on all the package features

* Initial docs setup
