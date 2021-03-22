from pyworkforce.shifts import MinAbsDifference, MinRequiredResources


def test_min_abs_difference_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    num_days = 2

    scheduler = MinAbsDifference(num_days=num_days,
                                 periods=24,
                                 shifts_coverage=shifts_coverage,
                                 required_resources=required_resources,
                                 max_period_concurrency=25,
                                 max_shift_concurrency=20)

    solution = scheduler.solve()

    assert solution['status'] == 'OPTIMAL'
    assert 'cost' in solution
    assert 'resources_shifts' in solution
    assert len(solution['resources_shifts']) == num_days * len(shifts_coverage)
    for i in range(num_days * len(shifts_coverage)):
        assert solution['resources_shifts'][i]['resources'] >= 0


def test_infeasible_min_abs_difference_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    num_days = 2

    scheduler = MinAbsDifference(num_days=num_days,
                                 periods=24,
                                 shifts_coverage=shifts_coverage,
                                 required_resources=required_resources,
                                 max_period_concurrency=10,
                                 max_shift_concurrency=20)

    solution = scheduler.solve()

    assert solution['status'] == 'INFEASIBLE'
    assert 'cost' in solution
    assert 'resources_shifts' in solution
    assert solution['cost'] == -1
    assert len(solution['resources_shifts']) == 1
    assert solution['resources_shifts'][0]['day'] == -1
    assert solution['resources_shifts'][0]['shift'] == 'Unknown'
    assert solution['resources_shifts'][0]['resources'] == -1


def test_min_required_resources_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    num_days = 2

    scheduler = MinRequiredResources(num_days=num_days,
                                     periods=24,
                                     shifts_coverage=shifts_coverage,
                                     required_resources=required_resources,
                                     max_period_concurrency=25,
                                     max_shift_concurrency=25)

    solution = scheduler.solve()

    assert solution['status'] == 'OPTIMAL'
    assert 'cost' in solution
    assert 'resources_shifts' in solution
    assert len(solution['resources_shifts']) == num_days * len(shifts_coverage)
    for i in range(num_days * len(shifts_coverage)):
        assert solution['resources_shifts'][i]['resources'] >= 0


def test_infeasible_min_required_resources_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    num_days = 2

    scheduler = MinRequiredResources(num_days=num_days,
                                     periods=24,
                                     shifts_coverage=shifts_coverage,
                                     required_resources=required_resources,
                                     max_period_concurrency=25,
                                     max_shift_concurrency=20)

    solution = scheduler.solve()

    assert solution['status'] == 'INFEASIBLE'
    assert 'cost' in solution
    assert 'resources_shifts' in solution
    assert solution['cost'] == -1
    assert len(solution['resources_shifts']) == 1
    assert solution['resources_shifts'][0]['day'] == -1
    assert solution['resources_shifts'][0]['shift'] == 'Unknown'
    assert solution['resources_shifts'][0]['resources'] == -1
