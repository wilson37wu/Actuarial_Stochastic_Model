"""
Data classes for policy and contract data.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy
)

@dataclass
class PolicyBase:
    """Base class for all insurance policies."""
    policy_number: str
    issue_date: date
    sum_assured: float
    premium: float
    sex: Sex
    underwriting_class: UnderwritingClass
    smoking_status: SmokingStatus
    occupation_class: OccupationClass

@dataclass
class TermPolicy(PolicyBase):
    """Term insurance policy data."""
    term_years: int
    product_type: ProductType = ProductType.TERM

@dataclass
class WholeLifePolicy(PolicyBase):
    """Whole life insurance policy data."""
    dividend_option: DividendOption = DividendOption.CASH
    investment_strategy: InvestmentStrategy = InvestmentStrategy.BALANCED
    product_type: ProductType = ProductType.WHOLE_LIFE

@dataclass
class ParticipatingPolicy(WholeLifePolicy):
    """Participating whole life insurance policy data."""
    bonus_rate: float = 0.0
    product_type: ProductType = ProductType.PARTICIPATING
