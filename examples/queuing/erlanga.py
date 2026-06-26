"""
Erlang A example: same scenario as the Erlang C example, but modeling customers
who abandon the queue if they wait too long.

Number of calls: 100
In a period of minutes: 30
Average Handling Time (minutes): 3
Average patience before abandoning (minutes): 5
Required Service Level: 80%
Target Answer Time (seconds): 20
Maximum Occupancy: 85%
Maximum Abandonment: 5%
Shrinkage: 30%
"""

from pyworkforce.queuing import ErlangA

erlang = ErlangA(transactions=100, aht=3, interval=30, asa=20 / 60,
                 patience=5, shrinkage=0.3)

requirements = erlang.required_positions(service_level=0.8,
                                         max_occupancy=0.85,
                                         max_abandonment=0.05)
print("requirements: ", requirements)

raw_positions = requirements["raw_positions"]
print("service_level: ", erlang.service_level(raw_positions))
print("abandonment_probability: ", erlang.abandonment_probability(raw_positions))
print("average_speed_of_answer (min): ", erlang.average_speed_of_answer(raw_positions))
print("average_queue_length: ", erlang.average_queue_length(raw_positions))
