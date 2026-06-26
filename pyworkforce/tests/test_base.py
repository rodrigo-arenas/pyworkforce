from pyworkforce.queuing import ErlangC, ErlangA
from pyworkforce.scheduling import MinRequiredResources


def test_get_params_roundtrip():
    erlang = ErlangC(transactions=100, aht=3, asa=20 / 60, interval=30, shrinkage=0.3)
    params = erlang.get_params()
    assert params == {
        "transactions": 100,
        "aht": 3,
        "asa": 20 / 60,
        "interval": 30,
        "shrinkage": 0.3,
    }
    # The params can rebuild an equivalent estimator.
    clone = ErlangC(**params)
    assert clone.get_params() == params


def test_repr_contains_class_and_params():
    erlang = ErlangA(transactions=100, aht=3, asa=0.33, interval=30, patience=5)
    text = repr(erlang)
    assert text.startswith("ErlangA(")
    assert "patience=5" in text


def test_repr_is_eval_friendly_for_simple_params():
    erlang = ErlangC(transactions=100, aht=3, asa=0.5, interval=30, shrinkage=0.1)
    namespace = {"ErlangC": ErlangC}
    clone = eval(repr(erlang), namespace)  # noqa: S307 - trusted local input
    assert clone.get_params() == erlang.get_params()


def test_scheduler_get_params_includes_stored_attributes():
    shifts_coverage = {"A": [1, 1, 0], "B": [0, 0, 1]}
    required = [[1, 1, 1]]
    scheduler = MinRequiredResources(num_days=1, periods=3,
                                     shifts_coverage=shifts_coverage,
                                     required_resources=required,
                                     max_period_concurrency=5,
                                     max_shift_concurrency=5)
    params = scheduler.get_params()
    assert params["num_days"] == 1
    assert params["periods"] == 3
    assert params["shifts_coverage"] == shifts_coverage
