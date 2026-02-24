"""
Actuarial Stochastic Model - A framework for actuarial modeling and analysis.
"""

from .models.data_generator import PolicyDataGenerator
from .models.data_classes import TermPolicy, WholeLifePolicy, ParticipatingPolicy
from .models.liabilities import (
    LiabilityModel, CashFlowProjection,
    MortalityTable, LapseAssumption, InflationAssumption,
)
from .models.products import (
    BaseInsuranceContract, TermInsurance, WholeLifeInsurance,
    PolicyValues, PolicyLoan,
)
from .enums import (
    Sex,
    UnderwritingClass,
    SmokingStatus,
    OccupationClass,
    ProductType,
    DividendOption,
    InvestmentStrategy,
)

__version__ = "0.1.0"

__all__ = [
    'PolicyDataGenerator',
    # Legacy simple dataclasses
    'TermPolicy',
    'WholeLifePolicy',
    'ParticipatingPolicy',
    # OOP product classes
    'BaseInsuranceContract',
    'TermInsurance',
    'WholeLifeInsurance',
    'PolicyValues',
    'PolicyLoan',
    # Liabilities
    'LiabilityModel',
    'CashFlowProjection',
    'MortalityTable',
    'LapseAssumption',
    'InflationAssumption',
    # Enums
    'Sex',
    'UnderwritingClass',
    'SmokingStatus',
    'OccupationClass',
    'ProductType',
    'DividendOption',
    'InvestmentStrategy',
]
