"""
Insurance risk capital calculation components.
References Cap 41R Part 5, Division 4.
"""

from .mortality import MortalityRiskModule
from .longevity import LongevityRiskModule
from .lapse import LapseRiskModule
from .aggregator import InsuranceRiskAggregator

__all__ = [
    'MortalityRiskModule',
    'LongevityRiskModule',
    'LapseRiskModule',
    'InsuranceRiskAggregator',
]
