"""
Liability model for insurance contracts.
"""
from datetime import date
from typing import List, Optional, Union

import pandas as pd

from .mortality import MortalityTable
from .lapse import LapseAssumption
from .inflation import InflationAssumption
from ..data_classes import TermPolicy, WholeLifePolicy, ParticipatingPolicy

class LiabilityModel:
    """Model for projecting insurance liabilities and cash flows."""
    
    def __init__(self,
                 mortality_table: MortalityTable,
                 lapse_assumption: LapseAssumption,
                 inflation_assumption: InflationAssumption,
                 minimum_dividend_rate: float = 0.01,
                 shareholder_cost_rate: float = 0.02):
        """Initialize the liability model with assumptions."""
        self.mortality_table = mortality_table
        self.lapse_assumption = lapse_assumption
        self.inflation_assumption = inflation_assumption
        self.minimum_dividend_rate = minimum_dividend_rate
        self.shareholder_cost_rate = shareholder_cost_rate
        self.contracts: List[Union[TermPolicy, WholeLifePolicy, ParticipatingPolicy]] = []
    
    def add_contract(self, contract: Union[TermPolicy, WholeLifePolicy, ParticipatingPolicy]) -> None:
        """Add an insurance contract to the model."""
        self.contracts.append(contract)
    
    def project_cashflows(self,
                         valuation_date: date,
                         projection_years: int = 50,
                         time_step: str = 'M',
                         export_assumptions: bool = False,
                         assumptions_file: Optional[str] = None) -> pd.DataFrame:
        """Project cash flows for all contracts.
        
        Args:
            valuation_date: Date to value the contracts from
            projection_years: Number of years to project
            time_step: Time step for projections ('M' for monthly, 'Q' for quarterly, 'Y' for yearly)
            export_assumptions: Whether to export assumptions to Excel
            assumptions_file: Path to save assumptions if exporting
            
        Returns:
            DataFrame with projected cash flows
        """
        if export_assumptions and assumptions_file:
            self._export_assumptions(assumptions_file)
        
        # Create a dummy cash flow projection for demonstration
        dates = pd.date_range(
            start=valuation_date,
            periods=projection_years * (12 if time_step == 'M' else 4 if time_step == 'Q' else 1),
            freq=time_step
        )
        
        cashflows = pd.DataFrame(index=dates)
        cashflows['Premium'] = 1000000 * (1 + self.inflation_assumption.get_rate(0))
        cashflows['Claims'] = 500000 * (1 + self.mortality_table.get_rate(40, 'M'))
        cashflows['Expenses'] = 100000 * (1 + self.inflation_assumption.get_rate(0, 'expense'))
        cashflows['Lapses'] = 50000 * self.lapse_assumption.get_rate(1, 'TERM')
        cashflows['Net_Cashflow'] = (
            cashflows['Premium'] -
            cashflows['Claims'] -
            cashflows['Expenses'] -
            cashflows['Lapses']
        )
        
        return cashflows
    
    def _export_assumptions(self, filepath: str) -> None:
        """Export model assumptions to Excel."""
        with pd.ExcelWriter(filepath) as writer:
            # Create dummy assumption tables for demonstration
            mortality_df = pd.DataFrame({
                'Age': range(0, 100),
                'Male_Rate': [0.001 * (1.1 ** (age // 10)) for age in range(0, 100)],
                'Female_Rate': [0.0008 * (1.1 ** (age // 10)) for age in range(0, 100)]
            })
            
            lapse_df = pd.DataFrame({
                'Duration': range(1, 11),
                'Term_Rate': [0.1 * (0.9 ** (dur - 1)) for dur in range(1, 11)],
                'Whole_Life_Rate': [0.05 * (0.9 ** (dur - 1)) for dur in range(1, 11)],
                'Par_Rate': [0.03 * (0.9 ** (dur - 1)) for dur in range(1, 11)]
            })
            
            inflation_df = pd.DataFrame({
                'Year': range(1, 51),
                'General': [0.02] * 50,
                'Medical': [0.04] * 50,
                'Expense': [0.03] * 50
            })
            
            mortality_df.to_excel(writer, sheet_name='Mortality_Rates', index=False)
            lapse_df.to_excel(writer, sheet_name='Lapse_Rates', index=False)
            inflation_df.to_excel(writer, sheet_name='Inflation_Rates', index=False)
