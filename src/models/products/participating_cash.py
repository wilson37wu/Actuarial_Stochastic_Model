"""
Participating whole life insurance product with cash dividends.
"""
from dataclasses import dataclass
from typing import List

from .whole_life import WholeLifeInsurance
from .data_classes import DividendHistory
from ..enums import ProductType, DividendOption, Sex

@dataclass
class ParticipatingWholeLifeCash(WholeLifeInsurance):
    """Participating whole life insurance contract with cash dividends."""
    
    def __init__(self, 
                 face_amount: float,
                 guaranteed_rate: float,
                 dividend_scale: float,
                 **kwargs):
        kwargs['product_type'] = ProductType.PAR_WHOLE_LIFE
        super().__init__(
            face_amount=face_amount,
            guaranteed_rate=guaranteed_rate,
            **kwargs
        )
        self.dividend_option = DividendOption.CASH
        self.dividend_scale = dividend_scale
        self.dividend_history: List[DividendHistory] = []
        self.asset_share: float = 0.0
    
    def calculate_asset_share(self,
                            duration: int,
                            mortality_rate: float,
                            expense_rate: float,
                            investment_return: float) -> float:
        """Calculate asset share using contribution method."""
        if duration == 0:
            self.asset_share = self.get_modal_premium()
        else:
            # Asset share formula:
            # Previous asset share accumulated with interest
            # Plus premium less expenses
            # Less cost of insurance
            # Less dividends paid
            previous_asset_share = self.asset_share
            premium = self.get_modal_premium()
            
            self.asset_share = (
                previous_asset_share * (1 + investment_return) +
                premium * (1 - expense_rate) - 
                self.face_amount * mortality_rate - 
                sum(div.amount for div in self.dividend_history
                    if div.declaration_date.year == self.issue_date.year + duration - 1)
            )
        
        return self.asset_share
    
    def calculate_dividend(self,
                          duration: int,
                          mortality_rate: float,
                          expense_rate: float,
                          investment_return: float) -> float:
        """Calculate cash dividend."""
        asset_share = self.calculate_asset_share(
            duration=duration,
            mortality_rate=mortality_rate,
            expense_rate=expense_rate,
            investment_return=investment_return
        )
        
        # Calculate Guaranteed Cash Value
        policy_year = duration // 12
        gcv = self.gcv_parameters.calculate_gcv(
            sex='M' if self.sex == Sex.MALE else 'F',
            policy_year=policy_year,
            premium=self.get_annual_premium(),
            face_amount=self.face_amount,
            pv_premium=self.get_premium_pv()
        )
        
        # Calculate non-guaranteed cash dividend
        # This is the excess of asset share over GCV, scaled by dividend scale
        cash_dividend = max(0, asset_share - gcv) * self.dividend_scale
        
        return cash_dividend 