import json
import os
from pyworkforce.rostering.binary_programming import MinHoursRoster

scheduler_data_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(scheduler_data_path, 'rostering_data.json'), 'r') as f:
    shifts_info = json.load(f)

solver = MinHoursRoster(num_days=shifts_info["num_days"],
                        resources=shifts_info["resources"],
                        shifts=shifts_info["shifts"],
                        shifts_hours=shifts_info["shifts_hours"],
                        min_working_hours=shifts_info["min_working_hours"],
                        max_resting=shifts_info["max_resting"],
                        non_sequential_shifts=shifts_info["non_sequential_shifts"],
                        banned_shifts=shifts_info["banned_shifts"],
                        required_resources=shifts_info["required_resources"],
                        resources_preferences=shifts_info["resources_preferences"],
                        resources_prioritization=shifts_info["resources_prioritization"])


results = solver.solve()


def test_expected_results():
    # The number of resting resources and shifted resources of all days
    # Must match with the list of resources per day
    assert len(results["resting_resource"]) + len(results["resource_shifts"]) == len(shifts_info["resources"])*shifts_info["num_days"]
    assert len(results["resource_shifts"]) == results["total_shifts"]
    assert results["status"] == 'OPTIMAL'
    assert results["total_resources"] == len(shifts_info["resources"])
    assert results["total_shifts"] == len(results["resource_shifts"])




