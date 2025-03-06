"""
Base class for insurance contracts.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from ..enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy, PremiumMode, NonForfeitureOption
)
from ..actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption,
    create_sample_mortality_table, create_sample_lapse_assumption,
    create_sample_inflation_assumption, ActuarialAssumptions
)
from ..gcv_calculator import GCVParameters, ProductVariant
from .data_classes import PolicyLoan, PolicyValues

@dataclass
class BaseInsuranceContract:
    """Base class for insurance contracts."""
    
    # Required fields (no defaults)
    policy_number: str
    issue_date: date
    product_type: ProductType
    face_amount: float
    issue_age: int
    sex: Sex
    term_length: Optional[int] = None  # None for whole life, number of years for term
    
    # Optional fields (with defaults)
    premium_mode: PremiumMode = PremiumMode.ANNUAL
    modal_premium: float = 0.0
    underwriting_class: UnderwritingClass = UnderwritingClass.STANDARD
    smoking_status: SmokingStatus = SmokingStatus.NON_SMOKER
    occupation_class: OccupationClass = OccupationClass.STANDARD
    
    # Product features
    dividend_option: DividendOption = DividendOption.CASH
    nonforfeiture_option: NonForfeitureOption = NonForfeitureOption.CASH_SURRENDER
    investment_strategy: Optional[InvestmentStrategy] = None
    
    # Product variant and GCV parameters
    product_variant: ProductVariant = ProductVariant.STANDARD
    gcv_parameters: Optional[GCVParameters] = None
    
    # Premium flexibility
    min_premium: Optional[float] = None
    max_premium: Optional[float] = None
    premium_holiday_available: bool = True
    max_premium_holiday: int = 12  # months
    current_premium_holiday: int = 0
    
    # Actuarial assumptions
    assumptions: ActuarialAssumptions = field(default_factory=ActuarialAssumptions)
    mortality_table: MortalityTable = field(init=False)
    lapse_assumption: LapseAssumption = field(init=False)
    inflation_assumption: InflationAssumption = field(init=False)
    
    def __post_init__(self):
        """Initialize actuarial assumptions after instance creation."""
        self.mortality_table = create_sample_mortality_table(self.assumptions)
        self.lapse_assumption = create_sample_lapse_assumption(self.assumptions)
        self.inflation_assumption = create_sample_inflation_assumption(self.assumptions)
    
    def get_attained_age(self, valuation_date: date) -> int:
        """Calculate attained age at valuation date."""
        if isinstance(valuation_date, pd.Timestamp):
            valuation_date = valuation_date.date()
        if isinstance(self.issue_date, pd.Timestamp):
            issue_date = self.issue_date.date()
        else:
            issue_date = self.issue_date
        years_since_issue = (valuation_date - issue_date).days / 365.25
        return self.issue_age + int(years_since_issue)
    
    def get_policy_duration(self, valuation_date: date) -> int:
        """Calculate policy duration in years."""
        if isinstance(valuation_date, pd.Timestamp):
            valuation_date = valuation_date.date()
        if isinstance(self.issue_date, pd.Timestamp):
            issue_date = self.issue_date.date()
        else:
            issue_date = self.issue_date
        return int((valuation_date - issue_date).days / 365.25)
    
    def is_active(self, valuation_date: date) -> bool:
        """Check if policy is still active."""
        try:
            if isinstance(valuation_date, pd.Timestamp):
                valuation_date = valuation_date.date()
            duration = self.get_policy_duration(valuation_date)
            
            # For whole life policies (term_length is None), they are active until death/surrender
            if self.term_length is None:
                return True
                
            return 0 <= duration < self.term_length
        except Exception as e:
            raise RuntimeError(f"Error checking policy active status: {str(e)}")
    
    def get_modal_premium(self) -> float:
        """Get modal premium based on premium mode."""
        if self.premium_mode == PremiumMode.ANNUAL:
            return self.modal_premium
        elif self.premium_mode == PremiumMode.SEMI_ANNUAL:
            return self.modal_premium / 2
        elif self.premium_mode == PremiumMode.QUARTERLY:
            return self.modal_premium / 4
        elif self.premium_mode == PremiumMode.MONTHLY:
            return self.modal_premium / 12
        else:
            raise ValueError(f"Unsupported premium mode: {self.premium_mode}")
    
    def get_annual_premium(self) -> float:
        """Get annual premium."""
        if self.premium_mode == PremiumMode.ANNUAL:
            return self.modal_premium
        elif self.premium_mode == PremiumMode.SEMI_ANNUAL:
            return self.modal_premium * 2
        elif self.premium_mode == PremiumMode.QUARTERLY:
            return self.modal_premium * 4
        elif self.premium_mode == PremiumMode.MONTHLY:
            return self.modal_premium * 12
        else:
            raise ValueError(f"Unsupported premium mode: {self.premium_mode}")
    
    def get_premium_pv(self, valuation_rate: float = 0.035) -> float:
        """Calculate present value of future premiums at time 0."""
        annual_premium = self.get_annual_premium()
        
        # Get mortality rates for each future year
        max_duration = 100 - self.issue_age  # Maximum duration to age 100
        mortality_rates = []
        for t in range(max_duration):
            attained_age = self.issue_age + t
            qx = self.mortality_table.get_rate(
                age=attained_age,
                sex=self.sex,
                smoking_status=self.smoking_status
            )
            mortality_rates.append(qx)
        
        # Calculate probability of survival to each year
        survival_probs = []
        cum_prob = 1.0
        for qx in mortality_rates:
            survival_probs.append(cum_prob)
            cum_prob *= (1 - qx)
        
        # Calculate present value
        pv = 0.0
        v = 1 / (1 + valuation_rate)
        for t in range(max_duration):
            pv += annual_premium * survival_probs[t] * (v ** t)
        
        return pv 