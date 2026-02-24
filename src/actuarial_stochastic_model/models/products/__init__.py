"""
Package for insurance product models.
"""
from .data_classes import PolicyLoan, PolicyValues, DividendHistory, BonusHistory
from .base import BaseInsuranceContract
from .term import TermInsurance
from .whole_life import WholeLifeInsurance

__all__ = [
    'BaseInsuranceContract',
    'PolicyLoan',
    'PolicyValues',
    'DividendHistory',
    'BonusHistory',
    'TermInsurance',
    'WholeLifeInsurance',
]
