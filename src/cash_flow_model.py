"""
Dynamic cash flow modeling for assets and liabilities with vectorized operations.

This module provides a comprehensive framework for modeling insurance cash flows using
vectorized operations for improved performance. It supports:

- Dynamic scenario modeling for both assets and liabilities
- Vectorized calculations using pandas operations
- Multiple economic scenarios analysis
- Risk metric calculations
- Integration with asset-liability management (ALM)

The main class DynamicCashFlowModel handles all cash flow projections and can be
used in conjunction with other modules for full ALM analysis.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union
from datetime import date
from src.economic_scenario import EconomicFactors
from .actuarial_calculations import ActuarialCalculations
import os
import datetime

class CashFlow:
    """
    Represents a single cash flow in the model.
    
    Attributes:
        amount (float): The monetary amount of the cash flow
        time_step (int): The time step at which the cash flow occurs
        flow_type (str): Type of cash flow (e.g., 'death_benefit', 'surrender_benefit', 'premium')
        policy_id (int): Identifier for the associated policy
        scenario_id (int): Identifier for the economic scenario (default: 0)
        date (date): The date of the cash flow (default: today)
    """
    def __init__(
            self,
            amount: float,
            time_step: int,
            flow_type: str,
            policy_id: int,
            scenario_id: int = 0,
            date: date = date.today()
        ):
        self.amount = amount
        self.time_step = time_step
        self.flow_type = flow_type
        self.policy_id = policy_id
        self.scenario_id = scenario_id
        self.date = date

class DynamicCashFlowModel:
    """
    Models dynamic cash flows for assets and liabilities using vectorized operations.
    
    This class provides high-performance cash flow modeling capabilities using pandas
    vectorized operations. It supports:
    
    - Multiple economic scenarios
    - Asset and liability cash flow projections
    - Risk metric calculations
    - Integration with investment strategies
    
    The model uses vectorized operations for improved performance while maintaining
    the flexibility to handle complex insurance product features.
    
    Args:
        initial_assets (float): Initial asset value
        mortality_table (pd.DataFrame): Mortality rates by age, sex, and other factors
        lapse_rates (Union[Dict[int, float], pd.Series]): Lapse rates by duration
        expense_factors (Union[Dict[str, float], pd.Series]): Expense factors by type
        investment_strategy (Dict[str, float]): Asset allocation strategy
    """
    def __init__(self, 
                 initial_assets: float,
                 mortality_table: pd.DataFrame,
                 lapse_rates: Union[Dict[int, float], pd.Series],
                 expense_factors: Union[Dict[str, float], pd.Series],
                 investment_strategy: Dict[str, float]):
        """Initialize the cash flow model."""
        self.initial_assets = initial_assets
        self.mortality_table = mortality_table
        self.lapse_rates = pd.Series(lapse_rates) if isinstance(lapse_rates, dict) else lapse_rates
        self.expense_factors = pd.Series(expense_factors) if isinstance(expense_factors, dict) else expense_factors
        self.investment_strategy = investment_strategy
        self.cash_flows: List[CashFlow] = []
        
    def _calculate_mortality_flows(self, policies: pd.DataFrame, valuation_date: date) -> pd.Series:
        """Vectorized mortality calculation using pandas operations."""
        # Calculate attained ages
        attained_ages = (valuation_date - pd.to_datetime(policies['date_of_birth'])).dt.days // 365
        
        # Merge with mortality rates
        merged = policies.merge(
            self.mortality_table,
            left_on=['sex', 'smoker_status', attained_ages],
            right_on=['sex', 'smoker_status', 'age'],
            how='left'
        )
        
        return merged['face_amount'] * merged['mortality_rate']

    def _calculate_lapse_flows(self, policies: pd.DataFrame, duration: int) -> pd.Series:
        """Calculate lapse benefits using vectorized operations."""
        lapse_rate = self.lapse_rates.loc[duration]
        return policies['account_value'] * 0.9 * lapse_rate  # 90% of account value

    def _calculate_expenses(self, policies: pd.DataFrame, time_step: str) -> pd.Series:
        """Calculate expenses using vectorized operations."""
        expense_rate = self.expense_factors[time_step]
        return policies['premium'] * expense_rate

    def project_liability_flows(
        self,
        economic_scenarios: List[List[EconomicFactors]],
        policy_data: pd.DataFrame
    ) -> List[CashFlow]:
        """Project liability cash flows for all scenarios using vectorized operations."""
        liability_flows = []
        
        for scenario_idx, scenario in enumerate(economic_scenarios):
            for time_idx, factors in enumerate(scenario):
                # Calculate benefits using vectorized operations
                death_flows = self._calculate_mortality_flows(policy_data, factors.date)
                surrender_flows = self._calculate_lapse_flows(policy_data, time_idx)
                expense_flows = self._calculate_expenses(policy_data, f"t{time_idx}")
                
                # Convert to CashFlow objects
                for policy_id, (death, surrender, expense) in enumerate(
                    zip(death_flows, surrender_flows, expense_flows)):
                    
                    if death > 0:
                        liability_flows.append(CashFlow(
                            death, time_idx, 'death_benefit', policy_id,
                            scenario_idx, factors.date
                        ))
                    
                    if surrender > 0:
                        liability_flows.append(CashFlow(
                            surrender, time_idx, 'surrender_benefit', policy_id,
                            scenario_idx, factors.date
                        ))
                    
                    if expense > 0:
                        liability_flows.append(CashFlow(
                            -expense, time_idx, 'expense', policy_id,
                            scenario_idx, factors.date
                        ))
                    
                    # Add premium inflow
                    if policy_data.iloc[policy_id]['premium'] > 0:
                        liability_flows.append(CashFlow(
                            policy_data.iloc[policy_id]['premium'],
                            time_idx, 'premium', policy_id,
                            scenario_idx, factors.date
                        ))
        
        return liability_flows
    
    def project_asset_flows(self,
                          economic_scenarios: List[List[EconomicFactors]],
                          liability_flows: List[CashFlow]) -> List[CashFlow]:
        """Project asset cash flows under given economic scenarios."""
        asset_flows = []
        
        for scenario_idx, scenario in enumerate(economic_scenarios):
            # Get liability flows for this scenario
            scenario_liabilities = [
                flow for flow in liability_flows 
                if flow.scenario_id == scenario_idx
            ]
            
            assets = self.initial_assets
            for time_idx, factors in enumerate(scenario):
                # Calculate investment income
                fixed_income_return = factors.short_rate + factors.credit_spread
                equity_return = factors.equity_return
                
                # Apply investment strategy using vectorized operations
                fixed_income_assets = assets * self.investment_strategy.get('fixed_income', 0.7)
                equity_assets = assets * self.investment_strategy.get('equity', 0.3)
                
                fixed_income_income = fixed_income_assets * fixed_income_return
                equity_income = equity_assets * (1 + equity_return)
                
                # Add investment flows
                asset_flows.append(CashFlow(
                    fixed_income_income + equity_income - assets,
                    time_idx,
                    'investment_return',
                    0,
                    scenario_idx,
                    factors.date
                ))
                
                # Update asset value for next period
                period_liability_flows = sum(
                    flow.amount for flow in scenario_liabilities
                    if flow.date == factors.date
                )
                assets = assets + fixed_income_income + equity_income + period_liability_flows
                
        return asset_flows
    
    def calculate_risk_metrics(self,
                             liability_flows: List[CashFlow],
                             asset_flows: List[CashFlow],
                             confidence_level: float = 0.95) -> Dict[str, float]:
        """Calculate key risk metrics from projected cash flows."""
        metrics = {}
        
        # Combine flows by scenario
        scenarios = {}
        for flow in liability_flows + asset_flows:
            if flow.scenario_id not in scenarios:
                scenarios[flow.scenario_id] = []
            scenarios[flow.scenario_id].append(flow)
            
        # Calculate metrics
        npvs = []
        for scenario_flows in scenarios.values():
            # Calculate NPV for each scenario
            discount_rate = 0.04  # Could be made more sophisticated
            npv = sum(
                flow.amount / (1 + discount_rate) ** (
                    (flow.date - date.today()).days / 365
                )
                for flow in scenario_flows
            )
            npvs.append(npv)
            
        # Calculate VaR
        npvs = np.array(npvs)
        metrics['var_95'] = np.percentile(npvs, (1 - confidence_level) * 100)
        
        # Calculate CTE (Conditional Tail Expectation)
        tail_losses = npvs[npvs <= metrics['var_95']]
        metrics['cte_95'] = np.mean(tail_losses) if len(tail_losses) > 0 else metrics['var_95']
        
        # Calculate other metrics
        metrics['mean_npv'] = np.mean(npvs)
        metrics['std_npv'] = np.std(npvs)
        metrics['skewness'] = (
            np.mean((npvs - metrics['mean_npv'])**3) / 
            metrics['std_npv']**3
        )
        
        return metrics

    def export_cash_flows(
        self,
        output_dir: str,
        economic_scenarios: List[List[EconomicFactors]],
        time_step: str = 'monthly'
    ) -> str:
        """
        Export cash flows to Excel with detailed breakdowns.
        
        Args:
            output_dir: Directory to save the Excel file
            economic_scenarios: List of economic scenarios for discounting
            time_step: 'monthly' or 'annual'
            
        Returns:
            str: Path to the created Excel file
        """
        # Create timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"cash_flows_{time_step}_{timestamp}.xlsx")
        
        # Convert cash flows to DataFrame
        df = pd.DataFrame([
            {
                'amount': cf.amount,
                'time_step': cf.time_step,
                'flow_type': cf.flow_type,
                'policy_id': cf.policy_id,
                'scenario_id': cf.scenario_id,
                'date': cf.date
            }
            for cf in self.cash_flows
        ])
        
        # Group cash flows by type
        flow_types = {
            'premium': df[df['flow_type'] == 'premium'],
            'death_benefit': df[df['flow_type'] == 'death_benefit'],
            'expense': df[df['flow_type'] == 'expense'],
            'surrender': df[df['flow_type'] == 'surrender'],
            'guaranteed_benefit': df[df['flow_type'].str.startswith('guaranteed_')],
            'non_guaranteed_benefit': df[df['flow_type'].str.startswith('non_guaranteed_')]
        }
        
        # Create Excel writer
        with pd.ExcelWriter(output_path) as writer:
            # Undiscounted cash flows
            time_periods = df['time_step'].unique()
            for flow_name, flow_data in flow_types.items():
                pivot = pd.pivot_table(
                    flow_data,
                    values='amount',
                    index='scenario_id',
                    columns='time_step',
                    aggfunc='sum',
                    fill_value=0
                )
                
                if time_step == 'annual' and 'monthly' in str(pivot.columns[0]):
                    # Convert monthly to annual if needed
                    pivot = pivot.groupby(pivot.columns // 12, axis=1).sum()
                
                pivot.to_excel(writer, sheet_name=f'{flow_name}_flows')
            
            # Present value calculations using forward rates
            for scenario_id, scenario in enumerate(economic_scenarios):
                # Extract rates for the scenario
                if time_step == 'annual':
                    rates = np.array([factor.short_rate for factor in scenario[::12]])  # Take every 12th rate
                else:
                    rates = np.array([factor.short_rate for factor in scenario])
                    rates = (1 + rates) ** (1/12) - 1  # Convert to monthly rates
                
                # Calculate discount factors
                discount_factors = np.cumprod(1 / (1 + rates))
                
                for flow_name, flow_data in flow_types.items():
                    # Filter for current scenario
                    scenario_flows = flow_data[flow_data['scenario_id'] == scenario_id]
                    
                    pivot = pd.pivot_table(
                        scenario_flows,
                        values='amount',
                        columns='time_step',
                        aggfunc='sum',
                        fill_value=0
                    )
                    
                    if time_step == 'annual' and 'monthly' in str(pivot.columns[0]):
                        pivot = pivot.groupby(pivot.columns // 12, axis=1).sum()
                    
                    # Apply scenario-specific discount factors
                    pv_flows = pivot * discount_factors[:pivot.shape[1]]
                    
                    # Append to existing sheet or create new one
                    sheet_name = f'{flow_name}_pv_scenario_{scenario_id}'
                    if len(sheet_name) > 31:  # Excel sheet name length limit
                        sheet_name = f'{flow_name[:20]}_pv_s{scenario_id}'
                    pv_flows.to_excel(writer, sheet_name=sheet_name)
        
        return output_path
