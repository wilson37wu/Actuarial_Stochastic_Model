"""
Module for Whole Life Insurance product.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ...enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy
)

@dataclass
class WholeLifeInsurance:
    """Class representing a whole life insurance contract."""
    policy_number: str
    issue_date: date
    sum_assured: float
    premium: float
    sex: Sex
    underwriting_class: UnderwritingClass
    smoking_status: SmokingStatus
    occupation_class: OccupationClass
    dividend_option: DividendOption
    investment_strategy: InvestmentStrategy
    
    @property
    def product_type(self) -> ProductType:
        """Get product type."""
        return ProductType.PARTICIPATING
    
    def get_sum_at_risk(self, valuation_date: date) -> float:
        """Get sum at risk at valuation date."""
        if valuation_date < self.issue_date:
            return 0.0
        else:
            return self.sum_assured  # Simplified, should consider cash value
