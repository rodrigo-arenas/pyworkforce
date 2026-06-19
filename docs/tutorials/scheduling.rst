Scheduling Problems
===================

Introduction
------------

In workforce management, scheduling means choosing how many resources to assign to each shift
based on projected demand by interval. For example, after using ErlangC to estimate hourly call
center requirements, scheduling can decide how many agents should be assigned to the available
morning, afternoon, night, or mixed shifts.

The meaning of "optimal" depends on the objective function. A schedule might minimize the total
number of scheduled resources, or it might minimize the absolute difference between required
and planned resources.

pyworkforce includes two scheduling solvers:

* MinAbsDifference
* MinRequiredResources

The following sections explain each method, first intuitively and then with the mathematical
formulation and examples.

For both methods, we'll introduce the following variables and notation:

=============== ==================  =====================================
Name            Type                Description
=============== ==================  =====================================
:math:`D`       Set                 Days on the planning horizon
:math:`S`       Set                 Shifts in a day
:math:`P`       Set                 Periods or intervals in a day
:math:`E_{sp}`  Parameter           1 if the shift `s` covers the period `p`, 0 otherwise
:math:`\beta`   Parameter           Maximum number of resources that are allowed in a shift
:math:`\gamma`  Parameter           Maximum number of resources that are allowed in a period
:math:`N_{dp}`  Parameter           Number of resources required at day `d` for the period `p`
:math:`X_{ds}`  Decision variable   Number of resources to schedule at day `d` for the shift `s`
=============== ==================  =====================================

The period definition can use any time granularity: 24 one-hour intervals, 48 half-hour intervals,
or another structure that matches your requirements data.


MinAbsDifference
----------------

This method minimizes the absolute difference between required and scheduled resources.
Because it minimizes differences in both directions, the solution may schedule more or fewer
resources than required in a given interval.

Under this definition, the objective function is formulated as:

.. math::

    min \sum_{d, p} \left | X_{ds}*E_{sp} - N_{dp} \right |

Notice that the term :math:`X_{ds}*E_{sp}` would result in the number of scheduled resources for a period
and day, and the term :math:`N_{dp}` is the required resources, so the objective is to minimize
the absolute difference over all days and periods of the requirements vs. the actual scheduling.

The model uses these restrictions:

* The number of scheduled resources for a period `p` and day `d` cannot exceed the maximum allowed capacity.

.. math::

    0 \leq X_{ds}*E_{sp} \leq \gamma \; \forall d \in  D, \forall p \in  P


* The number of scheduled resources on the same shift cannot exceed the maximum allowed capacity.

.. math::

    0 \leq X_{ds} \leq \beta \; \forall d \in  D, \forall s \in  S

* Positive integer restriction

.. math::

    X_{ds}, \gamma, N_{dp} \in \mathbb{Z}^{*} \; \forall d \in  D, \forall s \in  S, \forall p \in  P \\

* Boolean restriction

.. math::

    E_{sp} \in \{0, 1\} \; \forall s \in  S, \forall p \in  P \\

This is how to solve the problem with pyworkforce. The comments reference the notation above.
The example solves a two-day scheduling problem with 24 one-hour intervals per day.

.. code:: python3

   from pyworkforce.scheduling import MinAbsDifference
   from pprint import PrettyPrinter

   # Columns are an hour of the day, rows are the days
   # N_dp
   required_resources = [
       [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
       [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
   ]

   # Each shift has 24 entries, one per hour of the day
   # E_sp
   shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                      "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                      "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

   scheduler = MinAbsDifference(num_days=2,  # S
                                periods=24,  # P
                                shifts_coverage=shifts_coverage,
                                required_resources=required_resources,
                                max_period_concurrency=27,  # gamma
                                max_shift_concurrency=25)   # beta

   solution = scheduler.solve()
   pp = PrettyPrinter(indent=2)
   pp.pprint(solution)

The solver will print this solution:

.. code:: python3

   { 'cost': 157.0,
     'resources_shifts': [ {'day': 0, 'resources': 11, 'shift': 'Morning'},
                           {'day': 0, 'resources': 11, 'shift': 'Afternoon'},
                           {'day': 0, 'resources': 9, 'shift': 'Night'},
                           {'day': 0, 'resources': 1, 'shift': 'Mixed'},
                           {'day': 1, 'resources': 13, 'shift': 'Morning'},
                           {'day': 1, 'resources': 14, 'shift': 'Afternoon'},
                           {'day': 1, 'resources': 13, 'shift': 'Night'},
                           {'day': 1, 'resources': 0, 'shift': 'Mixed'}],
     'status': 'OPTIMAL'}

The ``OPTIMAL`` status means that the solver found the best feasible solution for the model.
The cost is the value of the objective function.
``resources_shifts`` is the shift schedule, represented by :math:`X_{ds}`; it tells you how many
resources to schedule for each day and shift.


MinRequiredResources
--------------------

This method minimizes the total scheduled resources while ensuring that every interval has at least
the required number of resources. It often schedules more resources than ``MinAbsDifference`` because
understaffing is not allowed.

In addition to the variables used by ``MinAbsDifference``, this method accepts an optional shift-cost
parameter:

=============== ==================  ========================================
Name            Type                Description
=============== ==================  ========================================
:math:`C_{s}`   Parameter            Cost or weight in the objective function for shift `s`
=============== ==================  ========================================


In this case, the objective function is:

.. math::

    min \sum_{d, s} C_{s}*X_{ds}


The model uses these restrictions:

* The number of scheduled resources for a period `p` and day `d` must be
  greater than or equal to the required resources for that day and period.

.. math::

    \sum_{d, p} X_{ds}*E_{sp} \geq  N_{dp} \; \forall d \in  D, \forall p \in  P

* The number of scheduled resources for a period `p` and day `d` cannot exceed the maximum allowed capacity.

.. math::

    0 \leq X_{ds}*E_{sp} \leq \gamma \; \forall d \in  D, \forall p \in  P


* The number of scheduled resources on the same shift cannot exceed the maximum allowed capacity.

.. math::

    0 \leq X_{ds} \leq \beta \; \forall d \in  D, \forall s \in  S

* Positive integer restriction

.. math::

    X_{ds}, \gamma, N_{dp} \in \mathbb{Z}^{*} \; \forall d \in  D, \forall s \in  S, \forall p \in  P \\

* Boolean restriction

.. math::

    E_{sp} \in \{0, 1\} \; \forall s \in  S, \forall p \in  P \\

This is how to solve the problem with pyworkforce. The comments reference the notation above.
The example solves a two-day scheduling problem with 24 one-hour intervals per day.

.. code:: python3

   from pyworkforce.scheduling import MinRequiredResources
   from pprint import PrettyPrinter

   # Columns are an hour of the day, rows are the days
   # N_dp
   required_resources = [
       [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
       [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
   ]

   # Each shift has 24 entries, one per hour of the day
   # E_sp
   shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                      "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                      "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

   # Optional cost for assigning one resource to each shift
   # C_s
   cost_dict = {"Morning": 1, "Afternoon": 1.2, "Night": 2, "Mixed": 1.5}

   scheduler = MinRequiredResources(num_days=2,  # S
                                    periods=24,  # P
                                    shifts_coverage=shifts_coverage,
                                    required_resources=required_resources,
                                    max_period_concurrency=27,  # gamma
                                    max_shift_concurrency=25)   # beta

   solution = scheduler.solve()
   pp = PrettyPrinter(indent=2)
   pp.pprint(solution)

The solver will print this solution:

.. code:: python3

   { 'cost': 113.0,
     'resources_shifts': [ {'day': 0, 'resources': 12, 'shift': 'Morning'},
                           {'day': 0, 'resources': 13, 'shift': 'Afternoon'},
                           {'day': 0, 'resources': 19, 'shift': 'Night'},
                           {'day': 0, 'resources': 6, 'shift': 'Mixed'},
                           {'day': 1, 'resources': 20, 'shift': 'Morning'},
                           {'day': 1, 'resources': 20, 'shift': 'Afternoon'},
                           {'day': 1, 'resources': 23, 'shift': 'Night'},
                           {'day': 1, 'resources': 0, 'shift': 'Mixed'}],
     'status': 'OPTIMAL'}

The ``OPTIMAL`` status means that the solver found the best feasible solution for the model.
The cost is the value of the objective function.
``resources_shifts`` is the shift schedule, represented by :math:`X_{ds}`; it tells you how many
resources to schedule for each day and shift.
