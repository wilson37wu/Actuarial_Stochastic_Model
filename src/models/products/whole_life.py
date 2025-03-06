"""
Whole life insurance product.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List

import pandas as pd

from .base import BaseInsuranceContract
from .data_classes import PolicyLoan, PolicyValues
from ..enums import ProductType, PremiumStatus

@dataclass
class WholeLifeInsurance(BaseInsuranceContract):
    """Whole life insurance contract."""
    
    def __init__(self, 
                 face_amount: float,
                 guaranteed_rate: float,
                 **kwargs):
        kwargs['product_type'] = ProductType.WHOLE_LIFE
        super().__init__(
            face_amount=face_amount,
            term_length=None,  # Whole life has no term
            **kwargs
        )
        self.guaranteed_rate = guaranteed_rate
        self.cash_values: Dict[int, float] = {}
        self.loans: List[PolicyLoan] = []
        self.premium_status = PremiumStatus.PAYING  # Initialize premium status
    
    def is_active(self, valuation_date: date) -> bool:
        """Check if policy is active at valuation date."""
        if isinstance(valuation_date, pd.Timestamp):
            valuation_date = valuation_date.date()
        
        # For whole life policies, they are active until death/surrender
        # Term length is not applicable
        duration = (valuation_date - self.issue_date).days / 365.25
        
        # Check if policy has lapsed or surrendered
        if self.premium_status in [PremiumStatus.LAPSED]:
            return False
        
        return True
    
    def calculate_nonforfeiture_values(self, 
                                     duration: int,
                                     valuation_rate: float) -> PolicyValues:
        """Calculate non-forfeiture values."""
        if duration not in self.cash_values:
            return PolicyValues(
                cash_value=0.0,
                surrender_value=0.0,
                death_benefit=0.0
            )
        
        cash_value = self.cash_values[duration]
        net_value = cash_value - sum(
            loan.amount + loan.outstanding_interest
            for loan in self.loans
        )
        
        # Calculate reduced paid-up insurance
        reduced_face = net_value / (
            (1 + valuation_rate) ** (100 - self.issue_age - duration)  # To age 100
        )
        
        # Calculate extended term insurance period
        monthly_cost = self.face_amount * 0.001  # Simplified monthly cost
        if monthly_cost > 0:
            extended_months = int(net_value / monthly_cost)
        else:
            extended_months = 0
        
        return PolicyValues(
            cash_value=cash_value,
            surrender_value=net_value * 0.95,  # 5% surrender charge
            death_benefit=self.face_amount,
            loan_balance=sum(loan.amount for loan in self.loans),
            reduced_paid_up_value=reduced_face,
            extended_term_period=extended_months
        ) 