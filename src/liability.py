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
                 inflation_assumption: InflationAssumption,
                 investment_returns: Optional[Dict[date, float]] = None,
                 gcv_factors: Optional[GCVFactors] = None,
                 minimum_dividend_rate: float = 0.01,
                 shareholder_cost_rate: float = 0.02):
        """Initialize liability model."""
        self.mortality_table = mortality_table
        self.lapse_assumption = lapse_assumption
        self.inflation_assumption = inflation_assumption
        self.investment_returns = investment_returns or {}
        self.gcv_calculator = GCVCalculator(external_factors=gcv_factors)
        self.dividend_tracker = DividendTracker(
            minimum_dividend_rate=minimum_dividend_rate,
            shareholder_cost_rate=shareholder_cost_rate
        )
        self.contracts: List[BaseInsuranceContract] = []
    
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
            
            # Track policy state
            remaining_if = 1.0  # Track remaining in-force
            current_values = PolicyValues(
                cash_value=0.0,
                surrender_value=0.0,
                death_benefit=contract.face_amount,
                loan_balance=0.0
            )
            
            for t, proj_date in enumerate(time_points):
                if remaining_if <= 0.001:  # Stop if less than 0.1% remaining in-force
                    break
                
                try:
                    # Get current rates
                    duration = contract.get_policy_duration(proj_date)
                    attained_age = contract.get_attained_age(proj_date)
                    
                    qx = self.mortality_table.get_rate(
                        age=attained_age,
                        sex=contract.sex,
                        smoking_status=contract.smoking_status
                    )
                    
                    wx = self.lapse_assumption.get_rate(
                        duration=duration,
                        product_type=contract.product_type
                    )
                    
                    # Calculate premium (deterministic)
                    if contract.premium_mode == PremiumMode.FLEXIBLE:
                        premium = min(
                            contract.max_premium or float('inf'),
                            max(
                                contract.min_premium or 0.0,
                                contract.get_modal_premium()
                            )
                        )
                    else:
                        premium = contract.get_modal_premium()
                    
                    # Handle premium payment status
                    if len(contract.premium_history) > 0:
                        last_payment = contract.premium_history[-1]
                        if last_payment.status == PremiumStatus.PREMIUM_HOLIDAY:
                            premium = 0.0
                        elif (last_payment.status == PremiumStatus.AUTOMATIC_PREMIUM_LOAN and
                              contract.nonforfeiture_option == NonForfeitureOption.AUTOMATIC_PREMIUM_LOAN):
                            if current_values.cash_value >= premium:
                                contract.loans.append(
                                    PolicyLoan(
                                        amount=premium,
                                        start_date=proj_date,
                                        interest_rate=0.08,  # Example rate
                                        purpose="PREMIUM"
                                    )
                                )
                                cf['policy_loans'][t] += premium * remaining_if
                            else:
                                cf['surrenders'][t] += current_values.surrender_value * remaining_if
                                remaining_if = 0
                                break
                    
                    # Update cash values based on product type
                    if contract.product_type == ProductType.UNIVERSAL_LIFE:
                        # UL account value mechanics (deterministic credited rate)
                        coi = contract.cost_of_insurance[attained_age]
                        credited_rate = max(
                            contract.min_guaranteed_rate,
                            contract.current_credited_rate
                        )
                        
                        current_values.cash_value = (
                            current_values.cash_value * (1 + credited_rate / 12) +
                            premium - 
                            coi * contract.face_amount / 1000
                        )
                        
                        current_values.death_benefit = contract.calculate_death_benefit()
                        
                    elif contract.product_type == ProductType.UNIT_LINKED:
                        # Unit-linked value mechanics (stochastic investment returns)
                        contract.update_allocation(proj_date)
                        investment_return = self.investment_returns.get(
                            proj_date,
                            0.05  # Default return
                        )
                        
                        # Update unit values stochastically
                        for fund, units in contract.unit_holdings.items():
                            nav = contract.nav_history.get((proj_date, fund), 1.0)
                            current_values.unit_value += units * nav * (
                                1 + investment_return - 
                                contract.fund_charges[fund]
                            )
                        
                        current_values.cash_value = current_values.unit_value
                        current_values.death_benefit = max(
                            contract.face_amount,
                            current_values.unit_value
                        )
                        
                    elif contract.product_type == ProductType.PAR_WHOLE_LIFE:
                        # Participating policy mechanics (stochastic investment returns)
                        investment_return = self.investment_returns.get(
                            proj_date,
                            0.05  # Default return
                        )
                        
                        # Calculate asset share and dividend (stochastic)
                        asset_share = contract.calculate_asset_share(
                            duration=duration,
                            mortality_rate=qx,
                            expense_rate=0.05,  # Example expense rate
                            investment_return=investment_return
                        )
                        
                        # Calculate Guaranteed Cash Value
                        policy_year = duration // 12
                        gcv = self.gcv_calculator.calculate_gcv(
                            sex='M' if contract.sex == Sex.MALE else 'F',
                            policy_year=policy_year,
                            premium=contract.get_annual_premium(),
                            face_amount=contract.face_amount,
                            pv_premium=contract.get_premium_pv()
                        )
                        
                        # Update cash and surrender values
                        current_values.cash_value = max(gcv, asset_share)
                        current_values.surrender_value = gcv  # Use GCV as surrender value
                        
                        # Calculate non-guaranteed cash dividend
                        cash_dividend = self.dividend_tracker.calculate_dividend(
                            policy_number=contract.policy_number,
                            asset_return=investment_return,
                            face_amount=contract.face_amount,
                            valuation_date=proj_date
                        )
                        
                        # Record cash dividend separately from other dividends
                        cf['cash_dividends'][t] += cash_dividend * remaining_if
                        
                        if duration > 0 and duration % 12 == 0:  # Annual dividend
                            # Calculate other dividends (e.g., experience refund)
                            experience_dividend = max(0, asset_share - gcv) * contract.dividend_scale
                            cf['experience_dividends'][t] += experience_dividend * remaining_if
                            
                            if contract.dividend_option == DividendOption.CASH:
                                current_values.dividend_balance += experience_dividend
                            elif contract.dividend_option == DividendOption.PREMIUM:
                                cf['premiums'][t] += experience_dividend * remaining_if
                            elif contract.dividend_option == DividendOption.ADDITIONS:
                                contract.face_amount += experience_dividend
                    
                    # Calculate decrements (deterministic mortality, potentially stochastic lapse)
                    prob_death = qx * (1 - wx/2)  # Independent decrements
                    prob_lapse = wx * (1 - qx/2)
                    
                    # Apply decrements to in-force (deterministic for mortality)
                    death_decrement = remaining_if * prob_death
                    lapse_decrement = remaining_if * prob_lapse
                    
                    # Record cash flows
                    cf['death_benefits'][t] += current_values.death_benefit * death_decrement
                    cf['surrenders'][t] += current_values.surrender_value * lapse_decrement
                    cf['premiums'][t] += premium * remaining_if
                    cf['expenses'][t] += premium * 0.05 * remaining_if  # Example expense rate
                    
                    # Update remaining in-force
                    remaining_if *= (1 - prob_death - prob_lapse)
                    
                    # Handle loan interest
                    for loan in contract.loans:
                        loan.accrue_interest(
                            (time_points[t] - time_points[t-1]).days / 365
                        )
                        cf['loan_repayments'][t] += (
                            loan.get_payment_amount() * remaining_if
                        )
                
                except Exception as e:
                    print(f"Error processing contract: {e}")
                    return cf
            
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
