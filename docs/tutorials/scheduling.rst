Scheduling Problems
===================

Introduction
------------

In workforce management, scheduling refers to finding the "optimal" way to schedule a set of
resources depending on the projected requirements demand per interval.
This may be, for example, finding how many call center agents to schedule per one-hour interval,  given
some demand (for instance, using ErlangC) and some restrictions.
The "optimal" criteria is defined under an objective function, for example, minimizing the overall
number of scheduled resources or the absolute difference between the required and the planned resources.

Pyworkforce comes with several methods that already choose  over the objective function and
its restrictions, which are:

* MinAbsDifference
* MinRequiredResources

In the following sections, we'll explain the mathematical formulation of each method, as well as giving
an intuitive description and examples on how to use them.

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
:math:`A_{ds}`  Decision variable   Number of resources to schedule at day `d` for the shift `s`
=============== ==================  =====================================

Notice that the definition of period allows splitting a day in any number of intervals; it may be 24
intervals of one hour, 48 intervals of 30 minutes, etc. It will depend on the granularity of the requirements.


MinAbsDifference
----------------

This method tries to minimize the absolute difference between the required and scheduled resources,
this implies that the scheduled resources may be higher or lower than the actual requirement.

Under this definition, the objective function is formulated as:

.. math::

    min \sum_{d, p} \left | A_{ds}*E_{sp} - N_{dp} \right |

Notice that the term :math:`A_{ds}*E_{sp}` would result in the number of scheduled resources for a period
and day, and the term :math:`N_{dp}` is the required resources, so the objective is to minimize
the absolute difference over all days and periods of the requirements vs. the actual scheduling.

Now we Introduce the restrictions of this model:

* The number of scheduled resources for a period `p` and day `d` can't exceed the maximum allowed capacity.

.. math::

    0 \leq A_{ds}*E_{sp} \leq \gamma \; \forall d \in  D, \forall p \in  P


* The number of scheduled resources on a same shift, can't exceed the maximum allowed capacity.

.. math::

    0 \leq A_{ds} \leq \beta \; \forall d \in  D, \forall s \in  S

* Positive integers restriction

.. math::

    A_{ds}, \gamma, N_{dp} \in \mathbb{Z}^{*} \; \forall d \in  D, \forall s \in  S, \forall p \in  P \\

* Bool restriction

.. math::

    E_{sp} \in \{0, 1\} \; \forall s \in  S, \forall p \in  P \\

Under the pyworkforce package, this is how you can solve this problem; the comments make the
reference to each variable under the notation.
In this example, we will solve the scheduling problem for a horizon of two days;
we split each day into 24 intervals of one hour.

.. code:: python3

   from pyworkforce.scheduling import MinAbsDifference
   from pprint import PrettyPrinter

   # Columns are an hour of the day, rows are the days
   # N_dp
   required_resources = [
       [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
       [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
   ]

   # Each entry of a shift, is an hour of the day (24 columns)
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

First, we see that the status is optimal; this means that the solver found an optimal feasible solution.
The cost is 157; this is the value of the objective function.
The resources_shifts dict is the actual shifts schedule; this tells you how many resources to schedule
per day and shift.


MinRequiredResources
--------------------

This method tries to minimize the total scheduled resources while not planning fewer resources than required for each interval.
This method generally results in a higher number of resources planned since it's not allowed to have a deficit on the requirements.

Additionally to the variables used in the MinAbsDifference method, we introduce an additional cost variable
which can help to weight the cost of scheduling a resource if a particular shift, this parameter is:

=============== ==================  ========================================
Name            Type                Description
=============== ==================  ========================================
:math:`C_{s}`   Parameter            Cost or weight in o.f for the shift `s`
=============== ==================  ========================================


In this case, the objective function is:

.. math::

    min \sum_{d, s} C_{s}*A_{ds}


Now we Introduce the restrictions of this model:

* The number of scheduled resources for a period `p` and day `d` must be
  greater or equals to the required resources for such day and period.

.. math::

    \sum_{d, p} A_{ds}*E_{sp} \geq  N_{dp} \; \forall d \in  D, \forall p \in  P

* The number of scheduled resources for a period `p` and day `d` can't exceed the maximum allowed capacity.

.. math::

    0 \leq A_{ds}*E_{sp} \leq \gamma \; \forall d \in  D, \forall p \in  P


* The number of scheduled resources on a same shift, can't exceed the maximum allowed capacity.

.. math::

    0 \leq A_{ds} \leq \beta \; \forall d \in  D, \forall s \in  S

* Positive integers restriction

.. math::

    A_{ds}, \gamma, N_{dp} \in \mathbb{Z}^{*} \; \forall d \in  D, \forall s \in  S, \forall p \in  P \\

* Bool restriction

.. math::

    E_{sp} \in \{0, 1\} \; \forall s \in  S, \forall p \in  P \\

Under the pyworkforce package, this is how you can solve this problem; the comments make the
reference to each variable under the notation.
In this example, we will solve the scheduling problem for a horizon of two days;
we split each day into 24 intervals of one hour.

.. code:: python3

   from pyworkforce.scheduling import MinRequiredResources
   from pprint import PrettyPrinter

   # Columns are an hour of the day, rows are the days
   # N_dp
   required_resources = [
       [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
       [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
   ]

   # Each entry of a shift, is an hour of the day (24 columns)
   # E_sp
   shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                      "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                      "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

   # The cost of shifting a resource if each shift, if present, solver will minimize the total cost
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

First, we see that the status is optimal; this means that the solver found an optimal feasible solution.
The cost is 113; this is the value of the objective function.
The resources_shifts dict is the actual shifts schedule; this tells you how many resources to schedule
per day and shift.