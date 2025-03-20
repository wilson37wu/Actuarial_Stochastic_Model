"""
Module for Term Insurance product.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ...enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType
)

@dataclass
class TermInsurance:
    """Class representing a term insurance contract."""
    policy_number: str
    issue_date: date
    term_years: int
    sum_assured: float
    premium: float
    sex: Sex
    underwriting_class: UnderwritingClass
    smoking_status: SmokingStatus
    occupation_class: OccupationClass
    
    @property
    def product_type(self) -> ProductType:
        """Get product type."""
        return ProductType.TERM
    
    @property
    def maturity_date(self) -> date:
        """Get maturity date."""
        return date(
            self.issue_date.year + self.term_years,
            self.issue_date.month,
            self.issue_date.day
        )
    
    def get_sum_at_risk(self, valuation_date: date) -> float:
        """Get sum at risk at valuation date."""
        if valuation_date < self.issue_date:
            return 0.0
        elif valuation_date > self.maturity_date:
            return 0.0
        else:
            return self.sum_assured
