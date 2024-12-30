"""
Dynamic cash flow modeling for assets and liabilities.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import date
from src.economic_scenario import EconomicFactors

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
            mortality_rates = pd.Series(
                [self.mortality_table.loc[age, 'mortality_rate'] 
                 for age in policy_data['age']],
                index=policy_data.index
            )
            
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
        mortality_rates: pd.Series,
        time_step: int
    ) -> List[CashFlow]:
        """Calculate death benefits for the current time step."""
        death_benefits = []
        
        # Generate random death probabilities for each policy
        for policy_id, policy in policy_data.iterrows():
            base_mortality = mortality_rates[policy_id]
            death_prob = np.random.uniform(0.001, 0.005) * base_mortality
            
            if np.random.random() < death_prob:
                benefit = CashFlow(
                    policy['face_amount'],
                    time_step,
                    'death_benefit',
                    policy_id,
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
