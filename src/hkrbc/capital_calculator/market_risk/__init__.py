"""
Market risk capital calculation components.
References Cap 41R Part 5, Division 3.
"""

from .interest_rate import InterestRateRiskModule
from .credit_spread import CreditSpreadRiskModule
from .equity import EquityRiskModule
from .property import PropertyRiskModule
from .currency import CurrencyRiskModule
from .aggregator import MarketRiskAggregator

__all__ = [
    'InterestRateRiskModule',
    'CreditSpreadRiskModule',
    'EquityRiskModule',
    'PropertyRiskModule',
    'CurrencyRiskModule',
    'MarketRiskAggregator'
]
