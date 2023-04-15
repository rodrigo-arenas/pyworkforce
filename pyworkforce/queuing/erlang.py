import warnings
import pandas as pd
import numpy as np
from math import exp, gamma
from pyworkforce.utils import ParameterGrid
from collections.abc import Iterable
from pydantic import BaseModel, ValidationError, validator, Field, root_validator
from pydantic.typing import Dict, Optional

# Import constants
from pyworkforce.queuing.queueing_constants import cErlangC_generic_variable_list

def raise_value_errors(message):
    """
    Raise validation errors
    """
    raise ValidationError(message)

class Erlang_c_data(BaseModel):
    f"""
    Contains the generic parameters expected for ErlangC. The model contains {cErlangC_generic_variable_list}
    
    Parameters
    ----------
    transactions: float,
        The number of total transactions that comes in an interval.
    aht: float,
        Average handling time of a transaction (minutes).
    asa: float,
        The required average speed of answer (minutes).
    interval: int,
        Interval length (minutes) where the transactions come in
    shrinkage: float,
        Percentage of time that an operator unit is not available.

    """
    transactions: float = Field(gt=0.0)
    aht: float= Field(gt=0.0)
    asa: float = Field(gt=0.0)    
    shrinkage: float = Field(0.0, ge=0.0, le=1.0)
    interval: int = Field(gt=0.0)
    service_level_target: float = Field(gt=0.0, le=1.0)
    achieved_service_level: Optional[float] = Field(gt=0.0, le=1.0)
    raw_positions: Optional[float] = Field(ge=0.0)
    positions: Optional[float] = Field(ge=0.0)
    maximum_occupancy: Optional[float] = Field(1.0, ge=0.0)
    waiting_probability: Optional[float] = Field(ge=0.0)
    achieved_occupancy: Optional[float] = Field(ge=0.0)
    intensity: Optional[float] = Field(gt=0.0) # set as optional for creation purposes, if user specified than check if calculation matches

    @root_validator
    def calculate_intensity(cls, values):
        """
        Calculates the intensity for Erlang calculations
        """
        
        intensity = (values["transactions"] / values["interval"]) * values['aht']
        if values['intensity'] is not None:
            # If exists check if user value makes sense
            if values['intensity'] != intensity:
                warnings.warn(f"specified intensity: {values['intensity']} does not match calculated intensity: {intensity}, please check if this is desired")
        else:
            # add value
            values['intensity'] = intensity

        return values

    def calculate_waiting_probability(self):
        """
        Returns the probability of waiting in the queue

        Parameters
        ----------
        positions: int,
            The number of positions to attend the transactions.

        """
        # Gamma distribution is extended to treat floats with factorials with n+1, this is the upper part of the erlang C equation
        substitution_position_estimate = (self.intensity** self.raw_positions / gamma(self.raw_positions+1)) * (self.raw_positions / (self.raw_positions-self.intensity) )

        #Sum of erlang series
        erlang_b = 1
        for position in np.arange(1, self.raw_positions, 1):
            erlang_b += (self.intensity**position) / gamma(position+1)
        
        self.waiting_probability = round(substitution_position_estimate / (erlang_b + substitution_position_estimate), 2)

    def calculate_service_level(self):
        """
        Returns the expected service level given a number of positions

        Parameters
        ----------

        positions: int,
            The number of positions attending.
        """

        self.calculate_waiting_probability()
        exponential = exp(-(self.raw_positions - self.intensity) * (self.asa / self.aht))

        self.achieved_service_level = round(max(0, 1-(self.waiting_probability * exponential)), 3)

    def calculate_achieved_occupancy(self):
        """
        Returns the expected occupancy of positions

        Parameters
        ----------

        positions: int,
            The number of raw positions

        """

        self.achieved_occupancy = round(self.intensity / self.raw_positions, 3)

    def calculate_required_positions(self):
        """
        Computes the requirements using erlangc.rst

        Parameters
        ----------

        service_level: float,
            Target service level
        max_occupancy: float,
            The maximum fraction of time that a transaction can occupy a position

        Returns
        -------

        raw_positions: int,
            The required positions assuming shrinkage = 0
        positions: int,
            The number of positions needed to ensure the required service level
        service_level: float,
            The fraction of transactions that are expected to be assigned to a position,
            before the asa time
        occupancy: float,
            The expected occupancy of positions
        waiting_probability: float,
            The probability of a transaction waiting in the queue
        """       
        # set positions is intensity + 1 for initalisation, otherwise equations will return 1 for SL.
        self.raw_positions = self.intensity + 1
        self.calculate_service_level()
        # Incremental increase of position estimate to reach service level
        while self.achieved_service_level < self.service_level_target:
            self.raw_positions += .1
            self.calculate_service_level()

        # Set resulting parameters based on final position estimate
        self.calculate_achieved_occupancy() 
        # Adjust estimate when max occopancy is reached
        if self.achieved_occupancy > self.maximum_occupancy:
            self.raw_positions = self.intensity / self.maximum_occupancy

        self.calculate_waiting_probability() 
        
        #Compensate calculated positions for shrinkage factor used.
        self.positions = round(self.raw_positions / (1 - self.shrinkage), 2)
    
class ErlangC(BaseModel):
    """
    """
    ### Parameter setup ###
    erlang_scenarios : Dict[str, Dict[str, Erlang_c_data]] # List of possible scenario's including subscenario's.
    
    ### Setup parameter grid and validate parameters ###
    @validator('erlang_scenarios', pre=True)
    def __create_parameter_grid__(cls, erlang_scenarios) -> dict():

        for scenario, scenario_parameters in erlang_scenarios.items():
            # Format parameter to interables if not provided
            for parameter, value in scenario_parameters.items():
                if not isinstance(value, Iterable):
                   scenario_parameters[parameter] = [value]
                
            sub_scenarios = list(ParameterGrid(scenario_parameters))
            sub_scenario_output = {}
            for sub_scenario in range(len(sub_scenarios)):
                #validate individual scenarios 
                sub_scenario_output.update(
                    {f"{scenario}.{sub_scenario}" :Erlang_c_data(**sub_scenarios[sub_scenario])}
                )
            erlang_scenarios[scenario] = sub_scenario_output
        return erlang_scenarios
    
    def results_to_dataframe(self) -> pd.DataFrame:
        """
        Returns erlang scenario objects to a dataframe
        """

        # Transform all classes of Erlang C towards dictionaries
        results = {main_scenario: {subscenario_name: dict(subscenario) for subscenario_name, subscenario in sub_scenarios.items()} for  main_scenario, sub_scenarios in self.erlang_scenarios.items()}
        # Transform nested dictionaries towards a dataframe

        scenario_frames = []
        for scenario_name, scenario in results.items():
            scenario_frame = pd.DataFrame.from_dict(scenario, orient='index').reset_index().rename(columns={'index':'subscenario'})
            scenario_frame.insert(0, 'scenario', scenario_name)
            scenario_frames.append(scenario_frame)
            
        return pd.concat(scenario_frames)
    
    def calculate_required_positions(self):
        """
        Calculate the required positions for handeling transactions according to Erlang C methodology
        """
       
        result = {main_scenario: {subscenario_name: subscenario.calculate_required_positions() for subscenario_name, subscenario in sub_scenarios.items()} for  main_scenario, sub_scenarios in self.erlang_scenarios.items()}
        

    def calculate_waiting_probability(self):
        """
        Returns the probability of waiting in the queue

        Parameters
        ----------
        positions: int,
            The number of positions to attend the transactions.

        """
        
        results = {main_scenario: {subscenario_name: subscenario.calculate_waiting_probability() for subscenario_name, subscenario in sub_scenarios.items()} for  main_scenario, sub_scenarios in self.erlang_scenarios.items()}


    def calculate_service_level(self):
        """
        Returns the expected service level given a number of positions

        Parameters
        ----------

        positions: int,
            The number of positions attending.
        scale_positions: bool, default = False
            Set it to True if the positions were calculated using shrinkage.

        """

        results = {main_scenario: {subscenario_name: subscenario.calculate_service_level() for subscenario_name, subscenario in sub_scenarios.items()} for  main_scenario, sub_scenarios in self.erlang_scenarios.items()}


    def calculate_achieved_occupancy(self):
        """
        Returns the expected occupancy of positions

        Parameters
        ----------

        positions: int,
            The number of raw positions

        """

        results = {main_scenario: {subscenario_name: subscenario.calculate_achieved_occupancy() for subscenario_name, subscenario in sub_scenarios.items()} for  main_scenario, sub_scenarios in self.erlang_scenarios.items()}        