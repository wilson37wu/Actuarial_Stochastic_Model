"""
Module for insurance product classes and features.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy, PremiumMode, PremiumStatus, NonForfeitureOption
)
from .actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption
)
from .investment import AssetClass, InvestmentPortfolio, TargetDateStrategy

class DividendOption(Enum):
    """Dividend payment options for participating policies."""
    CASH = auto()           # Pay in cash
    PREMIUM_REDUCTION = auto() # Reduce future premiums
    PAID_UP_ADDITIONS = auto() # Purchase additional insurance
    ACCUMULATE = auto()     # Accumulate with interest

class InvestmentStrategy(Enum):
    """Investment strategies for unit-linked products."""
    CONSERVATIVE = auto()   # Low risk, mostly bonds
    BALANCED = auto()       # Mix of stocks and bonds
    AGGRESSIVE = auto()     # High risk, mostly stocks
    LIFECYCLE = auto()      # Age-based allocation

class PremiumMode(Enum):
    """Premium payment modes."""
    ANNUAL = auto()
    SEMI_ANNUAL = auto()
    QUARTERLY = auto()
    MONTHLY = auto()
    SINGLE = auto()
    FLEXIBLE = auto()

class PremiumStatus(Enum):
    """Premium payment status."""
    PAYING = auto()
    PAID_UP = auto()
    REDUCED_PAID_UP = auto()
    PREMIUM_HOLIDAY = auto()
    AUTOMATIC_PREMIUM_LOAN = auto()
    LAPSED = auto()

class NonForfeitureOption(Enum):
    """Options when premium payment stops."""
    AUTOMATIC_PREMIUM_LOAN = auto()
    REDUCED_PAID_UP = auto()
    EXTENDED_TERM = auto()
    CASH_SURRENDER = auto()

@dataclass
class PremiumHistory:
    """Track premium payment history."""
    due_date: date
    amount_due: float
    amount_paid: float
    payment_date: Optional[date] = None
    payment_source: str = "CASH"  # CASH, LOAN, DIVIDEND
    status: PremiumStatus = PremiumStatus.PAYING

@dataclass
class PolicyLoan:
    """Represents a policy loan."""
    amount: float
    start_date: date
    interest_rate: float
    is_variable_rate: bool = False
    purpose: str = "GENERAL"  # GENERAL, PREMIUM, WITHDRAWAL
    outstanding_interest: float = 0.0
    
    def accrue_interest(self, days: int):
        """Accrue interest for given number of days."""
        daily_rate = self.interest_rate / 365
        interest = (self.amount + self.outstanding_interest) * (
            (1 + daily_rate) ** days - 1
        )
        self.outstanding_interest += interest

@dataclass
class DividendHistory:
    """Track dividend history."""
    declaration_date: date
    amount: float
    option: str  # CASH, PREMIUM, ADDITIONS, ACCUMULATE
    additions_amount: Optional[float] = None
    premium_offset: Optional[float] = None

@dataclass
class PolicyValues:
    """Represents various policy values."""
    cash_value: float
    surrender_value: float
    death_benefit: float
    loan_balance: float = 0.0
    dividend_balance: float = 0.0
    unit_value: float = 0.0
    reduced_paid_up_value: Optional[float] = None
    extended_term_period: Optional[int] = None  # in months

@dataclass
class BaseInsuranceContract:
    """Base class for insurance contracts."""
    policy_number: str
    issue_date: date
    term_length: int
    premium: float
    issue_age: int
    sex: Sex
    smoking_status: SmokingStatus
    occupation_class: OccupationClass
    underwriting_class: UnderwritingClass
    premium_mode: PremiumMode = PremiumMode.ANNUAL
    nonforfeiture_option: NonForfeitureOption = NonForfeitureOption.AUTOMATIC_PREMIUM_LOAN
    premium_history: List[PremiumHistory] = field(default_factory=list)
    premium_holiday_available: bool = True
    max_premium_holiday: int = 12  # months
    current_premium_holiday: int = 0
    
    def get_attained_age(self, valuation_date: date) -> int:
        """Calculate attained age at valuation date."""
        years_since_issue = (valuation_date - self.issue_date).days / 365.25
        return self.issue_age + int(years_since_issue)
    
    def get_policy_duration(self, valuation_date: date) -> int:
        """Calculate policy duration in years."""
        return int((valuation_date - self.issue_date).days / 365.25)
    
    def is_active(self, valuation_date: date) -> bool:
        """Check if policy is still active."""
        duration = self.get_policy_duration(valuation_date)
        return 0 <= duration < self.term_length
    
    def get_modal_premium(self) -> float:
        """Get premium amount based on payment mode."""
        if self.premium_mode == PremiumMode.ANNUAL:
            return self.premium
        elif self.premium_mode == PremiumMode.SEMI_ANNUAL:
            return self.premium / 2 * 1.02  # 2% loading
        elif self.premium_mode == PremiumMode.QUARTERLY:
            return self.premium / 4 * 1.03  # 3% loading
        elif self.premium_mode == PremiumMode.MONTHLY:
            return self.premium / 12 * 1.04  # 4% loading
        else:
            return 0.0  # Single premium or flexible
    
    def start_premium_holiday(self, start_date: date) -> bool:
        """Start premium holiday if available."""
        if (self.premium_holiday_available and 
            self.current_premium_holiday < self.max_premium_holiday):
            self.premium_history.append(
                PremiumHistory(
                    due_date=start_date,
                    amount_due=self.get_modal_premium(),
                    amount_paid=0.0,
                    status=PremiumStatus.PREMIUM_HOLIDAY
                )
            )
            self.current_premium_holiday += 1
            return True
        return False
    
    def end_premium_holiday(self):
        """End premium holiday."""
        if self.current_premium_holiday > 0:
            self.current_premium_holiday = 0
            return True
        return False

class TermInsurance(BaseInsuranceContract):
    """Term life insurance contract."""
    def __init__(self, face_amount: float, **kwargs):
        super().__init__(**kwargs)
        self.face_amount = face_amount
        self.product_type = ProductType.TERM

class WholeLifeInsurance(BaseInsuranceContract):
    """Whole life insurance contract."""
    def __init__(self, 
                 face_amount: float,
                 guaranteed_rate: float,
                 **kwargs):
        super().__init__(**kwargs)
        self.face_amount = face_amount
        self.guaranteed_rate = guaranteed_rate
        self.product_type = ProductType.WHOLE_LIFE
        self.cash_values: Dict[int, float] = {}
        self.loans: List[PolicyLoan] = []
    
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
            (1 + valuation_rate) ** (self.term_length - duration)
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

class ParticipatingWholeLife(WholeLifeInsurance):
    """Participating whole life insurance contract."""
    def __init__(self, 
                 dividend_option: DividendOption,
                 dividend_scale: float,
                 **kwargs):
        super().__init__(**kwargs)
        self.product_type = ProductType.PAR_WHOLE_LIFE
        self.dividend_option = dividend_option
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
            self.asset_share = self.premium
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

class UniversalLife(BaseInsuranceContract):
    """Universal life insurance contract."""
    def __init__(self,
                 initial_face_amount: float,
                 min_guaranteed_rate: float,
                 current_credited_rate: float,
                 cost_of_insurance: Dict[int, float],
                 min_premium: Optional[float] = None,
                 max_premium: Optional[float] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.product_type = ProductType.UNIVERSAL_LIFE
        self.face_amount = initial_face_amount
        self.min_guaranteed_rate = min_guaranteed_rate
        self.current_credited_rate = current_credited_rate
        self.cost_of_insurance = cost_of_insurance
        self.min_premium = min_premium
        self.max_premium = max_premium
        self.account_value = 0.0
        self.premium_history: Dict[date, float] = {}
        self.withdrawal_history: Dict[date, float] = {}
        self.loans: List[PolicyLoan] = []
        
        # Death benefit option
        self.death_benefit_option = "A"  # A: Level, B: Level + Account Value
    
    def change_death_benefit_option(self, new_option: str):
        """Change death benefit option."""
        if new_option in ["A", "B"]:
            self.death_benefit_option = new_option
            return True
        return False
    
    def calculate_death_benefit(self) -> float:
        """Calculate death benefit based on current option."""
        if self.death_benefit_option == "A":
            return max(self.face_amount, 
                      self.account_value * 1.01)  # Corridor requirement
        else:  # Option B
            return self.face_amount + self.account_value

class UnitLinkedInsurance(BaseInsuranceContract):
    """Unit-linked/Variable life insurance contract."""
    def __init__(self,
                 initial_face_amount: float,
                 investment_strategy: str,
                 fund_allocation: Dict[str, float],
                 fund_charges: Dict[str, float],
                 **kwargs):
        super().__init__(**kwargs)
        self.product_type = ProductType.UNIT_LINKED
        self.face_amount = initial_face_amount
        self.investment_strategy = investment_strategy
        
        # Initialize investment portfolio
        self.portfolio = InvestmentPortfolio(
            initial_allocation={
                AssetClass[k.upper()]: v 
                for k, v in fund_allocation.items()
            },
            asset_params=self._create_asset_params(fund_charges)
        )
        
        self.unit_holdings: Dict[str, float] = {}
        self.nav_history: Dict[Tuple[date, str], float] = {}
        self.switches: Dict[date, Dict[str, float]] = {}
        
        # Target date strategy if applicable
        self.target_date_strategy = None
        if "TARGET_" in investment_strategy:
            target_year = int(investment_strategy.split("_")[1])
            self.target_date_strategy = TargetDateStrategy(target_year)
    
    def _create_asset_params(self, 
                           fund_charges: Dict[str, float]
                           ) -> Dict[AssetClass, float]:
        """Create asset parameters for portfolio."""
        params = {}
        for fund, charge in fund_charges.items():
            asset = AssetClass[fund.upper()]
            if asset in [AssetClass.MONEY_MARKET, AssetClass.CASH]:
                params[asset] = {
                    'expected_return': 0.02,
                    'volatility': 0.01,
                    'duration': 0.25
                }
            elif asset in [AssetClass.GOVERNMENT_BOND, AssetClass.CORPORATE_BOND]:
                params[asset] = {
                    'expected_return': 0.04,
                    'volatility': 0.05,
                    'duration': 5.0,
                    'credit_spread': 0.01
                }
            else:  # Equity
                params[asset] = {
                    'expected_return': 0.08,
                    'volatility': 0.15,
                    'dividend_yield': 0.02
                }
        return params
    
    def update_allocation(self, valuation_date: date):
        """Update allocation based on investment strategy."""
        if self.target_date_strategy:
            new_allocation = self.target_date_strategy.get_allocation(
                valuation_date
            )
            self.portfolio.allocation = new_allocation

@dataclass
class ProductAssumptions:
    """Product-specific assumptions."""
    mortality: MortalityTable
    lapse: LapseAssumption
    inflation: InflationAssumption
    expense_per_policy: float
    investment_return: float
    dividend_scale_factor: float = 1.0
    crediting_spread: float = 0.015  # 1.5% spread for UL
    fund_performance: Dict[str, float] = None  # Fund returns
    partial_withdrawal_rate: float = 0.02
    policy_loan_rate: float = 0.06
    policy_loan_utilization: float = 0.1
    
    def __post_init__(self):
        if self.fund_performance is None:
            self.fund_performance = {
                'Money_Market': 0.02,
                'Bond': 0.04,
                'Balanced': 0.06,
                'Equity': 0.08
            }
