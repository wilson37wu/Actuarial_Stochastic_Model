"""
Module for liability modeling and cash flow projections.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
import os

import numpy as np
import pandas as pd

from .actuarial_assumptions import (
    MortalityTable, LapseAssumption, InflationAssumption
)
from ...enums import (
    Sex, ProductType, DividendOption, PremiumMode
)
from ...gcv_calculator import GCVCalculator, GCVFactors
from ...dividend_tracker import DividendTracker
from .products import (
    BaseInsuranceContract, PolicyValues
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
    
    def export_assumptions_to_excel(self, filepath: str, valuation_date: date) -> None:
        """Export all assumptions used in the model to Excel for audit purposes.
        
        Args:
            filepath: Path to save the Excel file
            valuation_date: Valuation date for the assumptions
        """
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Export mortality assumptions
                mortality_df = pd.DataFrame({
                    'Age': range(0, 121),
                    'Male_Rate': [self.mortality_table.get_rate(age, Sex.MALE) for age in range(0, 121)],
                    'Female_Rate': [self.mortality_table.get_rate(age, Sex.FEMALE) for age in range(0, 121)]
                })
                mortality_df.to_excel(writer, sheet_name='Mortality_Rates', index=False)
                
                # Export lapse assumptions
                lapse_df = pd.DataFrame({
                    'Policy_Year': range(1, 31),
                    'Base_Rate': [self.lapse_assumption.get_rate(year) for year in range(1, 31)],
                    'Dynamic_Factor': [self.lapse_assumption.get_dynamic_factor(year) for year in range(1, 31)]
                })
                lapse_df.to_excel(writer, sheet_name='Lapse_Rates', index=False)
                
                # Export inflation assumptions
                inflation_df = pd.DataFrame({
                    'Year': pd.date_range(start=valuation_date, periods=30, freq='Y').year,
                    'Rate': [self.inflation_assumption.get_rate(date) 
                            for date in pd.date_range(start=valuation_date, periods=30, freq='Y')]
                })
                inflation_df.to_excel(writer, sheet_name='Inflation_Rates', index=False)
                
                # Export investment returns if available
                if self.investment_returns:
                    returns_df = pd.DataFrame({
                        'Date': sorted(self.investment_returns.keys()),
                        'Return': [self.investment_returns[date] for date in sorted(self.investment_returns.keys())]
                    })
                    returns_df.to_excel(writer, sheet_name='Investment_Returns', index=False)
                
                # Export GCV factors if available
                if self.gcv_calculator.factors:
                    gcv_data = []
                    for duration in range(1, 31):
                        for age in range(20, 86, 5):
                            gcv_data.append({
                                'Duration': duration,
                                'Age': age,
                                'Factor': self.gcv_calculator.get_factor(duration, age)
                            })
                    gcv_df = pd.DataFrame(gcv_data)
                    gcv_df.to_excel(writer, sheet_name='GCV_Factors', index=False)
                
                # Export dividend assumptions
                dividend_df = pd.DataFrame({
                    'Parameter': ['Minimum_Dividend_Rate', 'Shareholder_Cost_Rate'],
                    'Value': [self.dividend_tracker.minimum_dividend_rate,
                             self.dividend_tracker.shareholder_cost_rate]
                })
                dividend_df.to_excel(writer, sheet_name='Dividend_Parameters', index=False)
                
        except Exception as e:
            raise RuntimeError(f"Error exporting assumptions to Excel: {str(e)}")

    def project_cashflows(self,
                         valuation_date: date,
                         projection_years: int,
                         time_step: str = 'M',
                         export_assumptions: bool = False,
                         assumptions_file: Optional[str] = None) -> pd.DataFrame:
        """Project cash flows for all contracts.
        
        Args:
            valuation_date: Starting date for projections
            projection_years: Number of years to project
            time_step: Time step for projections ('M' for monthly, 'Y' for yearly)
            export_assumptions: Whether to export assumptions to Excel
            assumptions_file: Path to save assumptions Excel file if export_assumptions is True
        
        Returns:
            DataFrame containing projected cash flows
        """
        if export_assumptions:
            if assumptions_file is None:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                assumptions_file = os.path.join(base_dir, 'assumptions_export.xlsx')
            self.export_assumptions_to_excel(assumptions_file, valuation_date)
        
        # Generate time points
        if time_step == 'M':
            time_points = pd.date_range(
                start=valuation_date,
                periods=projection_years * 12,
                freq='M'
            )
        else:  # Annual
            time_points = pd.date_range(
                start=valuation_date,
                periods=projection_years,
                freq='Y'
            )
        
        # Initialize cash flow arrays
        cf = {
            'Policy_Number': [],
            'Time_Point': [],
            'Premiums': [],
            'Death_Benefits': [],
            'Surrenders': [],
            'Expenses': [],
            'Cash_Dividends': [],
            'Experience_Dividends': [],
            'Policy_Loans': [],
            'Withdrawals': []
        }
        
        # Project each contract
        for contract in self.contracts:
            contract_cf = self._project_contract(
                contract=contract,
                time_points=time_points,
                valuation_date=valuation_date
            )
            
            # Add contract identifier
            contract_cf['Policy_Number'] = [contract.policy_number] * len(time_points)
            contract_cf['Time_Point'] = time_points
            
            # Append to main cash flows
            for key in cf:
                cf[key].extend(contract_cf[key])
        
        # Create DataFrame
        df = pd.DataFrame(cf)
        df.set_index('Time_Point', inplace=True)
        
        return df
    
    def _project_contract(self,
                         contract: BaseInsuranceContract,
                         time_points: List[date],
                         valuation_date: date
                         ) -> Dict[str, np.ndarray]:
        """Project cash flows for a single contract."""
        n_points = len(time_points)
        
        # Initialize cash flow arrays
        cf = {
            'Policy_Number': [],
            'Time_Point': [],
            'Premiums': np.zeros(n_points),
            'Death_Benefits': np.zeros(n_points),
            'Surrenders': np.zeros(n_points),
            'Expenses': np.zeros(n_points),
            'Cash_Dividends': np.zeros(n_points),
            'Experience_Dividends': np.zeros(n_points),
            'Policy_Loans': np.zeros(n_points),
            'Withdrawals': np.zeros(n_points)
        }
        
        # Initialize policy values
        current_values = PolicyValues(
            cash_value=0.0,
            surrender_value=0.0,
            death_benefit=contract.face_amount
        )
        
        # Track in-force amounts
        remaining_if = 1.0
        
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
                    cf['Cash_Dividends'][t] += cash_dividend * remaining_if
                    
                    if duration > 0 and duration % 12 == 0:  # Annual dividend
                        # Calculate other dividends (e.g., experience refund)
                        experience_dividend = max(0, asset_share - gcv) * contract.dividend_scale
                        cf['Experience_Dividends'][t] += experience_dividend * remaining_if
                        
                        if contract.dividend_option == DividendOption.CASH:
                            current_values.dividend_balance += experience_dividend
                        elif contract.dividend_option == DividendOption.PREMIUM:
                            cf['Premiums'][t] += experience_dividend * remaining_if
                        elif contract.dividend_option == DividendOption.PAID_UP_ADDITIONS:
                            contract.face_amount += experience_dividend
                
                # Calculate decrements (deterministic mortality, potentially stochastic lapse)
                prob_death = qx * (1 - wx/2)  # Independent decrements
                prob_lapse = wx * (1 - qx/2)
                
                # Apply decrements to in-force (deterministic for mortality)
                death_decrement = remaining_if * prob_death
                lapse_decrement = remaining_if * prob_lapse
                
                # Record cash flows
                cf['Death_Benefits'][t] += current_values.death_benefit * death_decrement
                cf['Surrenders'][t] += current_values.surrender_value * lapse_decrement
                cf['Premiums'][t] += premium * remaining_if
                cf['Expenses'][t] += premium * 0.05 * remaining_if
                
                # Update remaining in-force
                remaining_if -= (death_decrement + lapse_decrement)
                
            except Exception as e:
                print(f"Error projecting contract {contract.policy_number} at time {t}: {str(e)}")
                raise
        
        return cf
    
    def calculate_present_values(self, discount_rates: Dict[date, float]) -> Dict[str, float]:
        """Calculate present values of cash flows."""
        # Project cash flows
        projection = self.project_cashflows(
            valuation_date=min(discount_rates.keys()),
            projection_years=100,
            time_step='M'
        )
        
        # Calculate present values
        pv = {}
        for cf_type in ['Premiums', 'Death_Benefits', 'Surrenders', 'Expenses',
                       'Cash_Dividends', 'Experience_Dividends', 'Policy_Loans', 'Withdrawals']:
            if cf_type in projection.columns:
                pv[cf_type] = 0.0
                for t, row in projection.iterrows():
                    if t in discount_rates:
                        v = 1 / (1 + discount_rates[t])
                        pv[cf_type] += row[cf_type] * (v ** (t.month / 12))
        
        return pv

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
        df = cashflows.reset_index()  # Move Time_Point back to column
        
        # Calculate net liability
        df['Net_Liability'] = (
            df['Death_Benefits'] +
            df['Surrenders'] +
            df['Expenses'] +
            df['Cash_Dividends'] +
            df['Policy_Loans'] -
            df['Premiums'] -
            df['Loan_Repayments'] -
            df['Withdrawals']
        )
        
        # Add present value column (using 3% discount rate)
        time_years = [(d - valuation_date).days / 365.25 for d in df['Time_Point']]
        df['PV_Liability'] = df['Net_Liability'] / (1.03 ** np.array(time_years))
        
        return df
