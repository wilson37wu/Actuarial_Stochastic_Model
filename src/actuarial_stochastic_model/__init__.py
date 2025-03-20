"""
Actuarial Stochastic Model - A framework for actuarial modeling and analysis.
"""

from .models.data_generator import PolicyDataGenerator
from .models.data_classes import TermPolicy, WholeLifePolicy, ParticipatingPolicy
from .models.liabilities import (
    LiabilityModel, MortalityTable, LapseAssumption, InflationAssumption
)
from .enums import (
    Sex,
    UnderwritingClass,
    SmokingStatus,
    OccupationClass,
    ProductType,
    DividendOption,
    InvestmentStrategy
)

__version__ = "0.1.0"

__all__ = [
    'PolicyDataGenerator',
    'TermPolicy',
    'WholeLifePolicy',
    'ParticipatingPolicy',
    'LiabilityModel',
    'MortalityTable',
    'LapseAssumption',
    'InflationAssumption',
    'Sex',
    'UnderwritingClass',
    'SmokingStatus',
    'OccupationClass',
    'ProductType',
    'DividendOption',
    'InvestmentStrategy'
]
