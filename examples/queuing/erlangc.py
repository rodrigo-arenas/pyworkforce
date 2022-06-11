"""
Example taken from: https://www.callcentrehelper.com/erlang-c-formula-example-121281.htm

Requirement: Find the number of agents required to manage call center transactions
under the following parameters:

Number of calls: 100
In a period of minutes: 30
Average Handling Time (seconds): 180 (3 minutes)
Required Service Level: 80%
Target Answer Time (Seconds): 20
Maximum Occupancy: 85%
Shrinkage: 30%
"""

from pyworkforce.queuing import ErlangC

erlang = ErlangC(transactions=100, aht=3, interval=30, asa=20/60, shrinkage=0.3)

positions_requirements = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
print("positions_requirements: ", positions_requirements)

achieved_service_level = erlang.service_level(positions=positions_requirements['raw_positions'])
print("achieved_service_level: ", achieved_service_level)

achieved_service_level = erlang.service_level(positions=positions_requirements['positions'],
                                              scale_positions=True)
print("achieved_service_level: ", achieved_service_level)

waiting_probability = erlang.waiting_probability(positions=positions_requirements['raw_positions'])
print("waiting_probability: ", waiting_probability)

achieved_occupancy = erlang.achieved_occupancy(positions=positions_requirements['raw_positions'])
print("achieved_occupancy: ", achieved_occupancy)
