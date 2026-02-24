"""
Models package for actuarial stochastic modeling.
"""

from .data_generator import PolicyDataGenerator
from .data_classes import TermPolicy, WholeLifePolicy, ParticipatingPolicy
from .liabilities import (
    LiabilityModel,
    CashFlowProjection,
    MortalityTable,
    LapseAssumption,
    InflationAssumption,
)
from .products import (
    BaseInsuranceContract,
    TermInsurance,
    WholeLifeInsurance,
    PolicyValues,
    PolicyLoan,
)

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
]
