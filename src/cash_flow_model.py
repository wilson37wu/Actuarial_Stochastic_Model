"""
Dynamic cash flow modeling for assets and liabilities.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import date
from src.economic_scenario import EconomicFactors
from .actuarial_calculations import ActuarialCalculations
import os
import datetime

class CashFlow:
    """Represents a single cash flow in the model."""
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
    """Models dynamic cash flows for assets and liabilities."""
    
    def __init__(self, 
                 initial_assets: float,
                 mortality_table: pd.DataFrame,
                 lapse_rates: Dict[int, float],
                 expense_factors: Dict[str, float],
                 investment_strategy: Dict[str, float]):
        """Initialize the cash flow model."""
        self.initial_assets = initial_assets
        self.mortality_table = mortality_table
        self.lapse_rates = lapse_rates
        self.expense_factors = expense_factors
        self.investment_strategy = investment_strategy
        self.cash_flows: List[CashFlow] = []
        
    def project_liability_flows(
        self,
        economic_scenarios: List[List[EconomicFactors]],
        policy_data: pd.DataFrame
    ) -> List[CashFlow]:
        """Project liability cash flows for all scenarios."""
        liability_flows = []
        
        for scenario_idx, scenario in enumerate(economic_scenarios):
            # Get mortality rates for each policy based on age
            mortality_rates = [
                ActuarialCalculations.calculate_mortality_rates(
                    row['age'], 
                    row['sex'], 
                    self.mortality_table
                )
                for _, row in policy_data.iterrows()
            ]
            
            for time_idx, factors in enumerate(scenario):
                # Calculate benefits
                death_benefits = self._calculate_death_benefits(
                    policy_data, mortality_rates, time_idx)
                surrender_benefits = self._calculate_surrender_benefits(
                    policy_data, time_idx)
                
                # Project premiums
                premium_flows = self._calculate_premium_flows(
                    policy_data, time_idx)
                
                # Add flows to results
                for flow in death_benefits + surrender_benefits + premium_flows:
                    flow.scenario_id = scenario_idx
                    flow.date = factors.date
                    liability_flows.append(flow)
        
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
                
                # Apply investment strategy
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
    
    def _calculate_death_benefits(
        self,
        policy_data: pd.DataFrame,
        mortality_rates: List[float],
        time_step: int
    ) -> List[CashFlow]:
        """Calculate death benefits for the current time step."""
        death_benefits = []
        
        # Generate random death probabilities for each policy
        for policy_id, (policy, mortality_rate) in enumerate(zip(policy_data.iterrows(), mortality_rates)):
            # Assume Uniform Distribution of Deaths (UDD)
            q_x = mortality_rate  # Annual mortality rate
            t = 1/12  # Assuming monthly time steps
            death_prob = 1 - (1 - q_x) ** t  # Convert annual to monthly probability
            
            # Apply product-specific factors (example: multiplier for term life)
            product_factor = policy[1].get('mortality_factor', 1.0)
            death_prob *= product_factor
            
            if np.random.random() < death_prob:
                benefit = CashFlow(
                    policy[1]['face_amount'],
                    time_step,
                    'death_benefit',
                    policy[0],
                    0,
                    date.today()
                )
                death_benefits.append(benefit)
        
        return death_benefits
    
    def _calculate_surrender_benefits(
        self,
        policy_data: pd.DataFrame,
        time_step: int
    ) -> List[CashFlow]:
        """Calculate surrender benefits for the current time step."""
        surrender_benefits = []
        
        # Get lapse rate for current time step
        lapse_rate = self.lapse_rates.get(time_step, 0.05)  # Default to 5% if not specified
        
        for policy_id, policy in policy_data.iterrows():
            if np.random.random() < lapse_rate:
                surrender_value = policy['account_value'] * 0.9  # 90% of account value
                benefit = CashFlow(
                    surrender_value,
                    time_step,
                    'surrender_benefit',
                    policy_id,
                    0,
                    date.today()
                )
                surrender_benefits.append(benefit)
        
        return surrender_benefits
    
    def _calculate_premium_flows(
        self,
        policy_data: pd.DataFrame,
        time_step: int
    ) -> List[CashFlow]:
        """Calculate premium inflows for the current time step."""
        premium_flows = []
        
        for policy_id, policy in policy_data.iterrows():
            # Assume monthly premium payments
            if time_step % 12 == 0:  # Premium due at start of each year
                premium = CashFlow(
                    policy['premium'],
                    time_step,
                    'premium',
                    policy_id,
                    0,
                    date.today()
                )
                premium_flows.append(premium)
        
        return premium_flows
    
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
