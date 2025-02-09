import numpy as np
import pandas as pd
from datetime import date

class CashFlowEngine:
    """Centralized engine for actuarial cash flow calculations."""
    
    def __init__(self, mortality_table: pd.DataFrame, lapse_rates: pd.Series, expense_factors: pd.Series):
        self.mortality_table = mortality_table
        self.lapse_rates = lapse_rates
        self.expense_factors = expense_factors

    def calculate_mortality_flows(self, policies: pd.DataFrame, valuation_date: date) -> pd.Series:
        """Vectorized mortality calculation using pandas operations."""
        # Calculate attained ages
        attained_ages = (valuation_date - policies['date_of_birth']).dt.days // 365
        
        # Merge with mortality rates
        merged = policies.merge(
            self.mortality_table,
            left_on=['sex', 'smoker_status', attained_ages],
            right_on=['sex', 'smoker_status', 'age'],
            how='left'
        )
        
        return merged['sum_assured'] * merged['mortality_rate']

    def calculate_lapse_flows(self, policies: pd.DataFrame, duration: int) -> pd.Series:
        """Calculate lapse benefits using vectorized operations."""
        lapse_rates = self.lapse_rates.loc[duration].values
        return policies['surrender_value'] * lapse_rates

    def calculate_expenses(self, policies: pd.DataFrame, time_step: str) -> pd.Series:
        """Calculate expenses using vectorized operations."""
        expense_rates = self.expense_factors[time_step]
        return policies['premium'] * expense_rates

    def project_cashflows(self, policies: pd.DataFrame, economic_factors: pd.DataFrame) -> pd.DataFrame:
        """Project all cash flows in a single vectorized operation."""
        projections = pd.DataFrame({
            'date': economic_factors['date'],
            'mortality': self.calculate_mortality_flows(policies, economic_factors['date']),
            'lapse': self.calculate_lapse_flows(policies, economic_factors['duration']),
            'expense': self.calculate_expenses(policies, economic_factors['time_step'])
        })
        return projections
