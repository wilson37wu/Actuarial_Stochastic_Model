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
from .products import (
    BaseInsuranceContract, ProductType, PremiumStatus,
    NonForfeitureOption, PolicyValues
)

@dataclass
class CashFlowProjection:
    """Represents projected cash flows."""
    time_points: List[date]
    premiums: List[float]
    death_benefits: List[float]
    surrenders: List[float]
    expenses: List[float]
    dividends: List[float]
    policy_loans: List[float]
    loan_repayments: List[float]
    withdrawals: List[float]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert projections to DataFrame."""
        return pd.DataFrame({
            'Date': self.time_points,
            'Premium': self.premiums,
            'Death_Benefit': self.death_benefits,
            'Surrender': self.surrenders,
            'Expenses': self.expenses,
            'Dividends': self.dividends,
            'Policy_Loans': self.policy_loans,
            'Loan_Repayments': self.loan_repayments,
            'Withdrawals': self.withdrawals
        }).set_index('Date')
    
    def calculate_present_values(self, 
                               discount_rates: Dict[date, float]
                               ) -> Dict[str, float]:
        """Calculate present values of cash flows."""
        base_date = min(self.time_points)
        
        def discount(amount: float, val_date: date) -> float:
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
            'Net_Cashflow': sum(
                discount(
                    p - db - s - e - div - l + r - w,
                    d
                )
                for p, db, s, e, div, l, r, w, d in zip(
                    self.premiums,
                    self.death_benefits,
                    self.surrenders,
                    self.expenses,
                    self.dividends,
                    self.policy_loans,
                    self.loan_repayments,
                    self.withdrawals,
                    self.time_points
                )
            )
        }

class LiabilityModel:
    """Model for projecting insurance liabilities."""
    
    def __init__(self,
                 mortality_table: MortalityTable,
                 lapse_assumption: LapseAssumption,
                 inflation_assumption: InflationAssumption,
                 investment_returns: Optional[Dict[date, float]] = None):
        """Initialize liability model."""
        self.mortality_table = mortality_table
        self.lapse_assumption = lapse_assumption
        self.inflation_assumption = inflation_assumption
        self.investment_returns = investment_returns or {}
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
        
        time_points = pd.date_range(
            start=valuation_date,
            periods=periods,
            freq=freq
        ).to_list()
        
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
        
        return CashFlowProjection(
            time_points=time_points,
            premiums=premiums.tolist(),
            death_benefits=death_benefits.tolist(),
            surrenders=surrenders.tolist(),
            expenses=expenses.tolist(),
            dividends=dividends.tolist(),
            policy_loans=policy_loans.tolist(),
            loan_repayments=loan_repayments.tolist(),
            withdrawals=withdrawals.tolist()
        )
    
    def _project_contract(self,
                         contract: BaseInsuranceContract,
                         time_points: List[date],
                         valuation_date: date
                         ) -> Dict[str, np.ndarray]:
        """Project cash flows for a single contract."""
        n_points = len(time_points)
        cf = {
            'premiums': np.zeros(n_points),
            'death_benefits': np.zeros(n_points),
            'surrenders': np.zeros(n_points),
            'expenses': np.zeros(n_points),
            'dividends': np.zeros(n_points),
            'policy_loans': np.zeros(n_points),
            'loan_repayments': np.zeros(n_points),
            'withdrawals': np.zeros(n_points)
        }
        
        if not contract.is_active(valuation_date):
            return cf
        
        # Track policy state
        is_active = True
        current_values = PolicyValues(
            cash_value=0.0,
            surrender_value=0.0,
            death_benefit=contract.face_amount,
            loan_balance=0.0
        )
        
        for t, proj_date in enumerate(time_points):
            if not is_active:
                break
            
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
            
            # Calculate premium
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
            
            # Handle premium payment
            if len(contract.premium_history) > 0:
                last_payment = contract.premium_history[-1]
                if last_payment.status == PremiumStatus.PREMIUM_HOLIDAY:
                    premium = 0.0
                elif (last_payment.status == PremiumStatus.AUTOMATIC_PREMIUM_LOAN and
                      contract.nonforfeiture_option == NonForfeitureOption.AUTOMATIC_PREMIUM_LOAN):
                    # Create new policy loan
                    if current_values.cash_value >= premium:
                        contract.loans.append(
                            PolicyLoan(
                                amount=premium,
                                start_date=proj_date,
                                interest_rate=0.08,  # Example rate
                                purpose="PREMIUM"
                            )
                        )
                        cf['policy_loans'][t] += premium
                    else:
                        is_active = False
                        cf['surrenders'][t] += current_values.surrender_value
                        break
            
            # Update cash values based on product type
            if contract.product_type == ProductType.UNIVERSAL_LIFE:
                # UL account value mechanics
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
                # Unit-linked value mechanics
                contract.update_allocation(proj_date)
                investment_return = self.investment_returns.get(
                    proj_date,
                    0.05  # Default return
                )
                
                # Update unit values
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
                # Participating policy mechanics
                investment_return = self.investment_returns.get(
                    proj_date,
                    0.05  # Default return
                )
                
                # Calculate asset share and dividend
                asset_share = contract.calculate_asset_share(
                    duration=duration,
                    mortality_rate=qx,
                    expense_rate=0.05,  # Example expense rate
                    investment_return=investment_return
                )
                
                if duration > 0 and duration % 12 == 0:  # Annual dividend
                    dividend = max(0, asset_share * contract.dividend_scale)
                    cf['dividends'][t] += dividend
                    
                    if contract.dividend_option == DividendOption.CASH:
                        current_values.dividend_balance += dividend
                    elif contract.dividend_option == DividendOption.PREMIUM:
                        cf['premiums'][t] += dividend
                    elif contract.dividend_option == DividendOption.ADDITIONS:
                        contract.face_amount += dividend
                
            # Calculate probabilities of decrement
            prob_death = qx * (1 - wx/2)  # Independent decrements
            prob_lapse = wx * (1 - qx/2)
            
            # Apply decrements
            if np.random.random() < prob_death:
                cf['death_benefits'][t] += current_values.death_benefit
                is_active = False
                break
            elif np.random.random() < prob_lapse:
                cf['surrenders'][t] += current_values.surrender_value
                is_active = False
                break
            
            # Record cash flows
            cf['premiums'][t] += premium
            cf['expenses'][t] += premium * 0.05  # Example expense rate
            
            # Handle loan interest
            for loan in contract.loans:
                loan.accrue_interest(
                    (time_points[t] - time_points[t-1]).days
                    if t > 0 else 30
                )
            
            # Update surrender value
            current_values.surrender_value = max(
                0,
                current_values.cash_value * 0.95 -  # 5% surrender charge
                sum(loan.amount + loan.outstanding_interest 
                    for loan in contract.loans)
            )
        
        return cf
