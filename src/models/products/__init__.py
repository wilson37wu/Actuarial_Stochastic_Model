"""
Package for insurance product models.
"""
from .term_insurance import TermInsurance
from .whole_life_insurance import WholeLifeInsurance

__all__ = [
    'TermInsurance',
    'WholeLifeInsurance'
]