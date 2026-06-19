.. _erlangc_example:

Solving Queue Problems with ErlangC
===================================

This example estimates how many agents a call center needs to handle incoming calls.
Read the previous article first if you want the background behind the Erlang C formulation.

In this scenario, resources are agent stations and transactions are calls.

Let's assume that in a time interval of 30 minutes, there is an average of 100 incoming calls,
the AHT is 3 minutes, and the expected shrinkage is 30%.

As call center administrators, we want the average queue wait time to be 20 seconds
and the service level to be at least 80%.
We also want to ensure that the maximum occupancy of the agents is not greater than 85%.
The ``max_occupancy`` value must be greater than 0 and less than or equal to 1.

To solve this with pyworkforce, import ``ErlangC``, initialize it with the queue parameters,
and call ``required_positions``. All time variables must be expressed in minutes:

.. code:: python3

    from pyworkforce.queuing import ErlangC

    erlang = ErlangC(transactions=100, asa=20/60, aht=3, interval=30, shrinkage=0.3)

    requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
    print(requirements)

The output of this code should look like this:

.. code:: python3

    {'raw_positions': 14,
     'positions': 20,
     'service_level': 0.888,
     'occupancy': 0.714,
     'waiting_probability': 0.174}

The returned dictionary contains:

* **raw_positions:** Number of positions required before applying shrinkage
* **positions:** Number of positions required after applying shrinkage
* **service_level:** Expected percentage of transactions handled before the target ASA
* **occupancy:** Expected occupancy of the system
* **waiting_probability:** The probability that a transaction waits in the queue
