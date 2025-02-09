"""
Module for liability modeling and cash flow projections.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption
)
from .enums import (
    Sex, UnderwritingClass, SmokingStatus, OccupationClass,
    ProductType, DividendOption, InvestmentStrategy, PremiumMode, NonForfeitureOption,
    PremiumStatus
)
from .gcv_calculator import GCVCalculator, GCVFactors
from .dividend_tracker import DividendTracker
from .products import (
    BaseInsuranceContract, PolicyValues, PolicyLoan
)
from .cash_flow_model import DynamicCashFlowModel
from .actuarial_calculations import ActuarialCalculations

@dataclass
class CashFlowProjection:
    """Class to hold projected cash flows."""
    time_points: List[date]
    premiums: List[float]
    death_benefits: List[float]
    surrenders: List[float]
    expenses: List[float]
    dividends: List[float]
    policy_loans: List[float]
    loan_repayments: List[float]
    withdrawals: List[float]
    cash_dividends: List[float]
    experience_dividends: List[float]

    def __post_init__(self):
        """Convert time points to datetime.date if needed."""
        self.time_points = [
            t.date() if isinstance(t, pd.Timestamp) else t
            for t in self.time_points
        ]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert projections to DataFrame."""
        try:
            return pd.DataFrame({
                'Date': self.time_points,
                'Premium': self.premiums,
                'Death_Benefit': self.death_benefits,
                'Surrender': self.surrenders,
                'Expenses': self.expenses,
                'Dividends': self.dividends,
                'Policy_Loans': self.policy_loans,
                'Loan_Repayments': self.loan_repayments,
                'Withdrawals': self.withdrawals,
                'Cash_Dividends': self.cash_dividends,
                'Experience_Dividends': self.experience_dividends
            }).set_index('Date')
        except Exception as e:
            raise RuntimeError(f"Error converting projections to DataFrame: {str(e)}")

    def calculate_present_values(self, 
                               discount_rates: Dict[date, float]
                               ) -> Dict[str, float]:
        """Calculate present values of cash flows."""
        try:
            base_date = min(self.time_points)
            if isinstance(base_date, pd.Timestamp):
                base_date = base_date.date()
            
            def discount(amount: float, val_date: date) -> float:
                if isinstance(val_date, pd.Timestamp):
                    val_date = val_date.date()
                if val_date <= base_date:
                    return amount
                days = (val_date - base_date).days
                rate = discount_rates.get(val_date, 0.05)  # Default 5%
                return amount / ((1 + rate) ** (days / 365))
            
            return {
                'Premium': sum(
                    discount(p, d) 
                    for p, d in zip(self.premiums, self.time_points)
                ),
                'Death_Benefit': sum(
                    discount(db, d)
                    for db, d in zip(self.death_benefits, self.time_points)
                ),
                'Surrender': sum(
                    discount(s, d)
                    for s, d in zip(self.surrenders, self.time_points)
                ),
                'Expenses': sum(
                    discount(e, d)
                    for e, d in zip(self.expenses, self.time_points)
                ),
                'Dividends': sum(
                    discount(div, d)
                    for div, d in zip(self.dividends, self.time_points)
                ),
                'Policy_Loans': sum(
                    discount(l, d)
                    for l, d in zip(self.policy_loans, self.time_points)
                ),
                'Loan_Repayments': sum(
                    discount(r, d)
                    for r, d in zip(self.loan_repayments, self.time_points)
                ),
                'Withdrawals': sum(
                    discount(w, d)
                    for w, d in zip(self.withdrawals, self.time_points)
                ),
                'Cash_Dividends': sum(
                    discount(cd, d)
                    for cd, d in zip(self.cash_dividends, self.time_points)
                ),
                'Experience_Dividends': sum(
                    discount(ed, d)
                    for ed, d in zip(self.experience_dividends, self.time_points)
                ),
                'Net_Cashflow': sum(
                    discount(
                        p - db - s - e - div - l + r - w - cd - ed,
                        d
                    )
                    for p, db, s, e, div, l, r, w, cd, ed, d in zip(
                        self.premiums,
                        self.death_benefits,
                        self.surrenders,
                        self.expenses,
                        self.dividends,
                        self.policy_loans,
                        self.loan_repayments,
                        self.withdrawals,
                        self.cash_dividends,
                        self.experience_dividends,
                        self.time_points
                    )
                )
            }
        except Exception as e:
            raise RuntimeError(f"Error calculating present values: {str(e)}")

class LiabilityModel:
    """Model for projecting insurance liabilities."""
    
    def __init__(self,
                 mortality_table: MortalityTable,
                 lapse_assumption: LapseAssumption,
                 expense_factors: Dict[str, float],
                 investment_returns: Optional[Dict[date, float]] = None,
                 gcv_factors: Optional[GCVFactors] = None,
                 minimum_dividend_rate: float = 0.01,
                 shareholder_cost_rate: float = 0.02):
        """Initialize liability model."""
        self.mortality_table = mortality_table
        self.lapse_assumption = lapse_assumption
        self.expense_factors = expense_factors
        self.investment_returns = investment_returns or {}
        self.gcv_calculator = GCVCalculator(external_factors=gcv_factors)
        self.dividend_tracker = DividendTracker(
            minimum_dividend_rate=minimum_dividend_rate,
            shareholder_cost_rate=shareholder_cost_rate
        )
        self.contracts: List[BaseInsuranceContract] = []
        self.cash_flow_engine = DynamicCashFlowModel(
            mortality_table.data,
            lapse_assumption.rates,
            pd.Series(expense_factors)
        )
    
    def add_contract(self, contract: BaseInsuranceContract):
        """Add contract to model."""
        self.contracts.append(contract)
    
    def project_cashflows(self,
                         valuation_date: date,
                         projection_years: int,
                         time_step: str = 'M'  # 'M' for monthly, 'Q' for quarterly
                         ) -> CashFlowProjection:
        """Project cash flows for all contracts."""
        # Generate time points
        if time_step == 'M':
            periods = projection_years * 12
            freq = 'M'
        else:  # Quarterly
            periods = projection_years * 4
            freq = 'Q'
        
        # Convert all time points to datetime.date objects
        time_points = [
            d.date() if isinstance(d, pd.Timestamp) else d
            for d in pd.date_range(
                start=pd.Timestamp(valuation_date),
                periods=periods,
                freq=freq
            )
        ]
        
        # Initialize cash flow arrays
        n_points = len(time_points)
        premiums = np.zeros(n_points)
        death_benefits = np.zeros(n_points)
        surrenders = np.zeros(n_points)
        expenses = np.zeros(n_points)
        dividends = np.zeros(n_points)
        policy_loans = np.zeros(n_points)
        loan_repayments = np.zeros(n_points)
        withdrawals = np.zeros(n_points)
        cash_dividends = np.zeros(n_points)
        experience_dividends = np.zeros(n_points)
        
        # Project each contract
        for contract in self.contracts:
            cf = self._project_contract(
                contract, time_points, valuation_date
            )
            
            # Accumulate cash flows
            premiums += cf['premiums']
            death_benefits += cf['death_benefits']
            surrenders += cf['surrenders']
            expenses += cf['expenses']
            dividends += cf['dividends']
            policy_loans += cf['policy_loans']
            loan_repayments += cf['loan_repayments']
            withdrawals += cf['withdrawals']
            cash_dividends += cf['cash_dividends']
            experience_dividends += cf['experience_dividends']
        
        return CashFlowProjection(
            time_points=time_points,
            premiums=premiums.tolist(),
            death_benefits=death_benefits.tolist(),
            surrenders=surrenders.tolist(),
            expenses=expenses.tolist(),
            dividends=dividends.tolist(),
            policy_loans=policy_loans.tolist(),
            loan_repayments=loan_repayments.tolist(),
            withdrawals=withdrawals.tolist(),
            cash_dividends=cash_dividends.tolist(),
            experience_dividends=experience_dividends.tolist()
        )
    
    def _project_contract(self,
                         contract: BaseInsuranceContract,
                         time_points: List[date],
                         valuation_date: date
                         ) -> Dict[str, np.ndarray]:
        """Project cash flows for a single contract."""
        try:
            # Ensure valuation_date is datetime.date
            if isinstance(valuation_date, pd.Timestamp):
                valuation_date = valuation_date.date()
            
            # Convert time points to datetime.date if needed
            time_points = [
                t.date() if isinstance(t, pd.Timestamp) else t
                for t in time_points
            ]
            
            n_points = len(time_points)
            cf = {
                'premiums': np.zeros(n_points),
                'death_benefits': np.zeros(n_points),
                'surrenders': np.zeros(n_points),
                'expenses': np.zeros(n_points),
                'dividends': np.zeros(n_points),
                'policy_loans': np.zeros(n_points),
                'loan_repayments': np.zeros(n_points),
                'withdrawals': np.zeros(n_points),
                'cash_dividends': np.zeros(n_points),
                'experience_dividends': np.zeros(n_points)
            }
            
            if not contract.is_active(valuation_date):
                return cf
            
            # Mortality calculation
            mortality_rate = ActuarialCalculations.calculate_mortality_rates(
                age=contract.current_age,
                sex=contract.sex,
                mortality_table=self.mortality_table
            )

            # Lapse calculation
            lapse_rate = ActuarialCalculations.calculate_lapse_rates(
                duration=contract.duration,
                product_type=contract.product_type,
                lapse_assumptions=self.lapse_assumption
            )

            # Expense calculation
            expense = ActuarialCalculations.calculate_expenses(
                annual_premium=contract.premium,
                policy_duration=contract.duration,
                expense_factors=self.expense_factors
            )
            
            # Convert contract data to DataFrame
            policy_df = pd.DataFrame([contract.__dict__])
            
            # Get economic factors for projection period
            economic_factors = self._get_economic_factors(time_points)
            
            # Calculate all flows in one call
            projections = self.cash_flow_engine.project_cashflows(
                policy_df, 
                economic_factors
            )
            
            # Update cash flows
            cf['premiums'] = projections['premiums']
            cf['death_benefits'] = projections['death_benefits']
            cf['surrenders'] = projections['surrenders']
            cf['expenses'] = projections['expenses']
            cf['dividends'] = projections['dividends']
            cf['policy_loans'] = projections['policy_loans']
            cf['loan_repayments'] = projections['loan_repayments']
            cf['withdrawals'] = projections['withdrawals']
            cf['cash_dividends'] = projections['cash_dividends']
            cf['experience_dividends'] = projections['experience_dividends']
            
            return cf
        
        except Exception as e:
            print(f"Error processing contract: {e}")
            return cf

    def project_liabilities(self, n_years: int = 30) -> pd.DataFrame:
        """Project insurance liabilities over specified time period.
        
        Args:
            n_years: Number of years to project
            
        Returns:
            DataFrame with projected liability values
        """
        # Get current date
        valuation_date = date.today()
        
        # Project monthly cash flows
        cashflows = self.project_cashflows(
            valuation_date=valuation_date,
            projection_years=n_years,
            time_step='M'
        )
        
        # Convert to DataFrame
        df = cashflows.to_dataframe()
        df = df.reset_index()  # Move Date back to column
        
        # Calculate net liability
        df['Net_Liability'] = (
            df['Death_Benefit'] +
            df['Surrender'] +
            df['Expenses'] +
            df['Dividends'] +
            df['Policy_Loans'] -
            df['Premium'] -
            df['Loan_Repayments'] -
            df['Withdrawals']
        )
        
        # Add present value column (using 3% discount rate)
        time_years = [(d - valuation_date).days / 365.25 for d in df['Date']]
        df['PV_Liability'] = df['Net_Liability'] / (1.03 ** np.array(time_years))
        
        return df
