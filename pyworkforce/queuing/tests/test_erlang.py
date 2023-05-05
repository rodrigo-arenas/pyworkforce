import pytest
from pyworkforce.queuing import ErlangC

class TestDefaultErlangCBehaviour:
    """
    Test regular erlangC inputs for single and multi scenario dictionaries.
    """

    
    single_scenario_erlangC = {"test_scenario 1": {"transactions": 100, "aht": 3.0, "asa": .33, "shrinkage": 0.3, "interval": 30, 'service_level_target':.8}}
    multiple_parameter_erlangC = {"test_scenario 1": {"transactions": [100,200], "aht": [3.0, 5.0], "asa": [20 / 60, 1], "shrinkage": [0.3, .2], "interval": [15, 30], 'service_level_target':.8}}
    multiple_scenario_erlangC = {"test_scenario 1": {"transactions": 100, "aht": 3.0, "asa": 20 / 60, "shrinkage": 0.3, "interval": 30, 'service_level_target':.8},
                           "test_scenario 2": {"transactions": [100,200], "aht": 3.0, "asa": 20 / 60, "shrinkage": 0.3, "interval": 30, 'service_level_target':.8}}

    def test_erlangc_single_scenario_results_legacy(self):
        
        erlang = ErlangC(erlang_scenarios=self.single_scenario_erlangC)
        erlang.calculate_required_positions()
        results = erlang.results_to_dataframe()
        results = results.round(3)
        assert (results['raw_positions'] == 14).all()
        assert (results['positions'] == 19).all()
        assert (results['achieved_service_level'] == 0.888).all()
        assert (results['achieved_occupancy'] == 0.714).all()
        assert (results['waiting_probability'] == 0.174).all()

    def test_erlangc_single_scenario_results(self):
        
        erlang = ErlangC(erlang_scenarios=self.single_scenario_erlangC)
        erlang.calculate_required_positions(enforce_trafficking_requirements=False)
        results = erlang.results_to_dataframe()
        results = results.round(3)

        assert (results['raw_positions'] == 13.1).all()
        assert (results['positions'] == 18.714).all()
        assert (results['achieved_service_level'] == 0.817).all()
        assert (results['achieved_occupancy'] == 0.763).all()
        assert (results['waiting_probability'] == 0.257).all()

            