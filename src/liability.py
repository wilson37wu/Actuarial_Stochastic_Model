"""
Module for handling insurance liability cash flows.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

@dataclass
class InsuranceContract:
    """Represents an insurance contract with deterministic cash flows."""
    id: str
    issue_date: date
    maturity_date: date
    premium_pattern: Dict[date, float]  # {date: premium amount}
    benefit_pattern: Dict[date, float]  # {date: benefit amount}
    expense_pattern: Dict[date, float]  # {date: expense amount}
    currency: str = 'USD'

class LiabilityModel:
    """Model for projecting insurance liability cash flows."""
    
    def __init__(self, contracts: List[InsuranceContract]):
        """Initialize the liability model with a list of insurance contracts."""
        self.contracts = contracts
        self._validate_contracts()
    
    def _validate_contracts(self):
        """Validate the contracts data."""
        for contract in self.contracts:
            if contract.issue_date > contract.maturity_date:
                raise ValueError(f"Contract {contract.id}: Issue date cannot be after maturity date")
            
            # Ensure all cash flow dates are between issue and maturity
            all_dates = (list(contract.premium_pattern.keys()) + 
                        list(contract.benefit_pattern.keys()) + 
                        list(contract.expense_pattern.keys()))
            
            invalid_dates = [d for d in all_dates 
                           if d < contract.issue_date or d > contract.maturity_date]
            if invalid_dates:
                raise ValueError(f"Contract {contract.id}: Cash flow dates {invalid_dates} "
                               "are outside contract period")

    def project_cashflows(self, 
                         valuation_date: date,
                         projection_years: int = 100,
                         frequency: str = 'monthly') -> pd.DataFrame:
        """
        Project liability cash flows for the specified period.
        
        Args:
            valuation_date: Starting date for projections
            projection_years: Number of years to project (default: 100)
            frequency: Projection frequency ('monthly' or 'annual')
            
        Returns:
            DataFrame with projected cash flows containing:
                - date: projection date
                - contract_id: identifier of the contract
                - premium: premium cash flow
                - benefit: benefit cash flow
                - expense: expense cash flow
                - net_cashflow: net cash flow (premium - benefit - expense)
        """
        # Generate projection dates
        if frequency == 'monthly':
            periods = projection_years * 12
            freq = 'M'
        elif frequency == 'annual':
            periods = projection_years
            freq = 'Y'
        else:
            raise ValueError("Frequency must be either 'monthly' or 'annual'")
            
        projection_dates = pd.date_range(
            start=valuation_date,
            periods=periods + 1,  # +1 to include the start date
            freq=freq
        )
        
        # Initialize results DataFrame
        results = []
        
        for contract in self.contracts:
            # Skip if contract matured before valuation date
            if contract.maturity_date < valuation_date:
                continue
                
            contract_cf = pd.DataFrame(index=projection_dates)
            contract_cf['contract_id'] = contract.id
            
            # Function to aggregate cash flows within each period
            def aggregate_cashflows(pattern: Dict[date, float], dates: pd.DatetimeIndex) -> pd.Series:
                cf_series = pd.Series(0.0, index=dates)
                for cf_date, amount in pattern.items():
                    if cf_date < valuation_date:
                        continue
                    # Find the corresponding period for the cash flow
                    period_idx = dates.searchsorted(cf_date)
                    if period_idx < len(dates):
                        cf_series.iloc[period_idx] += amount
                return cf_series
            
            # Project each cash flow type
            contract_cf['premium'] = aggregate_cashflows(contract.premium_pattern, projection_dates)
            contract_cf['benefit'] = aggregate_cashflows(contract.benefit_pattern, projection_dates)
            contract_cf['expense'] = aggregate_cashflows(contract.expense_pattern, projection_dates)
            
            # Calculate net cash flow
            contract_cf['net_cashflow'] = (contract_cf['premium'] - 
                                         contract_cf['benefit'] - 
                                         contract_cf['expense'])
            
            results.append(contract_cf)
        
        if not results:
            # Return empty DataFrame with correct columns if no active contracts
            return pd.DataFrame(columns=['date', 'contract_id', 'premium', 
                                      'benefit', 'expense', 'net_cashflow'])
        
        # Combine all contracts and reset index to make date a column
        final_df = pd.concat(results, axis=0).reset_index()
        final_df.rename(columns={'index': 'date'}, inplace=True)
        
        return final_df.sort_values(['date', 'contract_id'])
