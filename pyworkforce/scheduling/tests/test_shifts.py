import numpy as np
import pytest

from pyworkforce.breaks import BreakScheduler
from pyworkforce.scheduling import MinAbsDifference, MinRequiredResources


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


def test_min_abs_difference_can_leave_demand_above_capacity_uncovered():
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

    assert solution['status'] == 'OPTIMAL'
    coverage = scheduler.coverage()
    assert coverage['scheduled'].max() <= 10
    assert coverage['shortfall'].max() >= 13
    assert solution['cost'] == (coverage['shortfall'] + coverage['surplus']).sum()


@pytest.mark.parametrize('scheduler_class', [MinAbsDifference, MinRequiredResources])
def test_shift_limits_and_coverage_for_named_demand_scenarios(scheduler_class):
    scheduler = scheduler_class(
        num_days=2, periods=3, shifts_coverage={'early': [1, 1, 0], 'late': [0, 1, 1]},
        required_resources=[[2, 3, 1], [1, 2, 2]], max_period_concurrency=3, max_shift_concurrency=3,
        shift_limits={(0, 'early'): (2, 3), (0, 'late'): (0, 1), (1, 'early'): (1, 1), (1, 'late'): (2, 2)},
        num_search_workers=1,
    )
    result = scheduler.solve()
    assert result['status'] == 'OPTIMAL'
    assert scheduler.solver.parameters.num_search_workers == 1
    assert scheduler.scheduled_resources() == {'early': [2, 1], 'late': [1, 2]}
    assert scheduler.coverage().to_records(index=False).tolist() == [
        (0, 0, 2, 2, 0, 0), (0, 1, 3, 3, 0, 0), (0, 2, 1, 1, 0, 0),
        (1, 0, 1, 1, 0, 0), (1, 1, 2, 3, 0, 1), (1, 2, 2, 2, 0, 0),
    ]
    comparison = scheduler.compare_coverage({'base': None, 'busy': [[2, 3, 1], [2, 4, 2]]})
    assert comparison.to_dict('records') == [
        {'scenario': 'base', 'required': 11, 'scheduled': 12, 'shortfall': 0, 'surplus': 1, 'understaffed_periods': 0},
        {'scenario': 'busy', 'required': 14, 'scheduled': 12, 'shortfall': 2, 'surplus': 0, 'understaffed_periods': 2},
    ]
    assert scheduler.solution_ is result


@pytest.mark.parametrize('scheduler_class', [MinAbsDifference, MinRequiredResources])
def test_shift_minimum_preserves_staffing_with_zero_demand(scheduler_class):
    scheduler = scheduler_class(1, 1, {'early': [1]}, [[0]], 3, 3,
                                shift_limits={(0, 'early'): (2, 3)})
    assert scheduler.solve()['status'] == 'OPTIMAL'
    assert scheduler.scheduled_resources() == {'early': [2]}


@pytest.mark.parametrize(('scheduler_class', 'status'), [(MinAbsDifference, 'OPTIMAL'), (MinRequiredResources, 'INFEASIBLE')])
def test_shift_maximum_limits_staffing_even_when_demand_is_higher(scheduler_class, status):
    scheduler = scheduler_class(1, 1, {'early': [1]}, [[3]], 3, 3,
                                shift_limits={(0, 'early'): (0, 1)})
    result = scheduler.solve()
    assert result['status'] == status
    if status == 'OPTIMAL':
        assert scheduler.scheduled_resources() == {'early': [1]}


@pytest.mark.parametrize('limits', [[], {0: (0, 1)}, {(2, 'early'): (0, 1)}, {(0, 'missing'): (0, 1)},
                                   {(0, 'early'): (2, 1)}, {(0, 'early'): (False, 2)}])
def test_rejects_invalid_shift_limits(limits):
    with pytest.raises(ValueError, match='shift_limits'):
        MinAbsDifference(1, 1, {'early': [1]}, [[1]], 3, 3, shift_limits=limits)


def test_coverage_requires_a_feasible_plan_and_rejects_invalid_scenarios():
    scheduler = MinRequiredResources(1, 1, {'early': [1]}, [[1]], 3, 3)
    with pytest.raises(RuntimeError, match='solve'):
        scheduler.coverage()
    scheduler.solve()
    with pytest.raises(ValueError, match='scenarios'):
        scheduler.compare_coverage({})
    for demand in ([[1, 2]], [[-1]], [[1.5]], [[2**63]]):
        with pytest.raises(ValueError, match='required_resources'):
            scheduler.coverage(demand)

    blocked = MinAbsDifference(1, 1, {'early': [1], 'late': [1]}, [[1]], 3, 3,
                               shift_limits={(0, 'early'): (2, 2), (0, 'late'): (2, 2)})
    assert blocked.solve()['status'] == 'INFEASIBLE'
    with pytest.raises(RuntimeError, match='INFEASIBLE'):
        blocked.scheduled_resources()


def test_coverage_uses_the_last_solved_plan_even_if_mutable_inputs_change():
    demand = [[2, 2]]
    shifts = {'early': [1, 1]}
    scheduler = MinRequiredResources(1, 2, shifts, demand, 3, 3, num_search_workers=1)
    result = scheduler.solve()
    demand[0][1] = 3
    shifts['early'][1] = 0
    result['resources_shifts'][0]['resources'] = 1
    result['status'] = 'UNKNOWN'
    assert scheduler.scheduled_resources() == {'early': [2]}
    scheduler.scheduled_resources()['early'][0] = 0
    assert scheduler.coverage()[['required', 'scheduled']].values.tolist() == [[2, 2], [2, 2]]

    assert scheduler.solve()['status'] == 'INFEASIBLE'
    with pytest.raises(RuntimeError, match='INFEASIBLE'):
        scheduler.coverage()


def test_compare_coverage_preserves_exact_totals_for_large_scenario_counts():
    scheduler = MinRequiredResources(1, 2, {'early': [1, 1]}, [[1, 1]], 3, 3)
    scheduler.solve()
    comparison = scheduler.compare_coverage({'large': [[2**62, 2**62]]}).iloc[0]
    assert comparison['required'] == 2**63
    assert comparison['shortfall'] == 2**63 - 2


def test_coverage_keeps_integer_precision_for_unsigned_coverage_masks():
    count = 2**53 + 1
    shifts = {'early': np.array([1], dtype=np.uint64)}
    scheduler = MinRequiredResources(1, 1, shifts, [[count]], count, count, num_search_workers=1)
    assert scheduler.solve()['status'] == 'OPTIMAL'
    assert scheduler.coverage()[['required', 'scheduled', 'shortfall']].values.tolist() == [[count, count, 0]]


def test_solved_shift_plan_feeds_the_break_scheduler():
    shifts = {'early': [1, 1]}
    schedule = MinRequiredResources(1, 2, shifts, [[2, 2]], 2, 2, num_search_workers=1)
    schedule.solve()
    breaks = BreakScheduler(
        1, 2, shifts, schedule.scheduled_resources(), [{'name': 'rest', 'duration_periods': 1}],
        [[1, 1]], num_search_workers=1,
    ).solve()
    assert breaks['status'] == 'OPTIMAL'
    assert sorted(entry['start_period'] for entry in breaks['break_schedule']) == [0, 1]


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


def test_cost_min_required_resources_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    cost_dict = {"Morning": 8, "Afternoon": 8, "Night": 10, "Mixed": 7}

    num_days = 2

    scheduler = MinRequiredResources(num_days=num_days,
                                     periods=24,
                                     shifts_coverage=shifts_coverage,
                                     required_resources=required_resources,
                                     cost_dict=cost_dict,
                                     max_period_concurrency=25,
                                     max_shift_concurrency=25)

    solution = scheduler.solve()

    assert solution['status'] == 'OPTIMAL'
    assert 'cost' in solution
    assert 'resources_shifts' in solution
    assert len(solution['resources_shifts']) == num_days * len(shifts_coverage)
    for i in range(num_days * len(shifts_coverage)):
        assert solution['resources_shifts'][i]['resources'] >= 0


def test_wrong_cost_min_required_resources_schedule():
    required_resources = [
        [9, 11, 17, 9, 7, 12, 5, 11, 8, 9, 18, 17, 8, 12, 16, 8, 7, 12, 11, 10, 13, 19, 16, 7],
        [13, 13, 12, 15, 18, 20, 13, 16, 17, 8, 13, 11, 6, 19, 11, 20, 19, 17, 10, 13, 14, 23, 16, 8]
    ]
    shifts_coverage = {"Morning": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "Afternoon": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                       "Night": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                       "Mixed": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]}

    cost_dict = {"Morning": 8, "Night": 10, "Mixed": 7}

    num_days = 2
    with pytest.raises(Exception) as excinfo:
        scheduler = MinRequiredResources(num_days=num_days,
                                         periods=24,
                                         shifts_coverage=shifts_coverage,
                                         required_resources=required_resources,
                                         cost_dict=cost_dict,
                                         max_period_concurrency=25,
                                         max_shift_concurrency=25)

        solution = scheduler.solve()
        assert str(excinfo.value) == "cost_dict must have the same keys as shifts_coverage"


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
