import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ProcessPoolExecutor
import logging

class ALMError(Exception):
    pass

class ALMEngine:
    """Asset-Liability Management Engine for stochastic projections."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.liability_model = None
        self.asset_model = None
        self.scenarios = None
        self.rebalancing_threshold = config.get('rebalancing_threshold', 0.05)  # 5% threshold
        self.target_allocation = config.get('target_allocation', {'bond': 0.6, 'equity': 0.4})
        self.dashboard = None  # Initialize dashboard
        
    def set_liability_model(self, liability_model):
        """Set the liability cash flow model."""
        self.liability_model = liability_model
        
    def set_asset_model(self, asset_model):
        """Set the asset cash flow model."""
        self.asset_model = asset_model
        
    def set_economic_scenarios(self, scenarios: Dict):
        """Set economic scenarios for projection."""
        self.scenarios = scenarios
        
    def run_stochastic_projection(self, num_scenarios: int, 
                                projection_years: int) -> Dict:
        """Run full stochastic projection across scenarios."""
        try:
            if self.liability_model is None or self.asset_model is None:
                raise ValueError("Both liability and asset models must be set")
                
            results = []
            with ProcessPoolExecutor() as executor:
                futures = []
                for scenario_idx in range(num_scenarios):
                    future = executor.submit(self._run_single_scenario, 
                                          scenario_idx, projection_years)
                    futures.append(future)
                    
                results = [f.result() for f in futures]
                
            return self._aggregate_results(results)
        except Exception as e:
            self._handle_error(e)
            raise ALMError(f"Projection failed: {str(e)}")
    
    def _handle_error(self, error):
        logging.error(f"ALM Engine Error: {error}")
        self.dashboard.update_error_status(error)
        
    def _run_single_scenario(self, scenario_idx: int, 
                           projection_years: int) -> Dict:
        """Run projection for a single scenario."""
        monthly_steps = projection_years * 12
        
        # Initialize tracking arrays
        portfolio_values = np.zeros(monthly_steps)
        liability_values = np.zeros(monthly_steps)
        asset_cashflows = np.zeros(monthly_steps)
        liability_cashflows = np.zeros(monthly_steps)
        surplus = np.zeros(monthly_steps)
        
        # Get scenario data
        scenario_rates = {
            'short_rate': self.scenarios['short_rate'][:, scenario_idx],
            'credit_spread': self.scenarios['credit_spread'][:, scenario_idx],
            'equity_return': self.scenarios['equity_return'][:, scenario_idx],
            'inflation': self.scenarios['inflation'][:, scenario_idx]
        }
        
        # Initial portfolio setup
        portfolio = self.asset_model.portfolio
        initial_assets = portfolio.total_assets
        
        for t in range(monthly_steps):
            # 1. Project liability cash flows
            liability_cf = self.liability_model.project_cashflows(
                valuation_date=pd.Timestamp.now() + pd.DateOffset(months=t),
                projection_years=1/12,  # One month projection
                time_step='M'
            )
            liability_cashflows[t] = sum(liability_cf.values())
            
            # 2. Project asset cash flows
            asset_cf = self.asset_model.project_cashflows(
                scenario_rates=scenario_rates,
                current_time=t
            )
            asset_cashflows[t] = sum(asset_cf.values())
            
            # 3. Portfolio rebalancing check
            current_allocation = portfolio.get_current_allocation()
            max_deviation = max(
                abs(current_allocation[asset] - target)
                for asset, target in self.target_allocation.items()
            )
            
            if max_deviation > self.rebalancing_threshold:
                trades = portfolio.rebalance()
                # Execute trades
                for asset_class, amount in trades.items():
                    if amount > 0:  # Buy
                        self.asset_model.reinvest_proceeds(amount, asset_class)
                    else:  # Sell
                        self.asset_model.sell_assets(-amount, asset_class)
            
            # 4. Reinvest net cash flows
            net_cf = asset_cashflows[t] - liability_cashflows[t]
            if net_cf > 0:
                # Reinvest surplus according to target allocation
                for asset_class, target_pct in self.target_allocation.items():
                    amount = net_cf * target_pct
                    self.asset_model.reinvest_proceeds(amount, asset_class)
            
            # 5. Update values
            portfolio_values[t] = portfolio.get_total_value(
                accounting_method=portfolio.accounting_method
            )
            liability_values[t] = self.liability_model.project_liabilities(1/12)[0]
            surplus[t] = portfolio_values[t] - liability_values[t]
        
        return {
            'scenario_idx': scenario_idx,
            'portfolio_values': portfolio_values,
            'liability_values': liability_values,
            'asset_cashflows': asset_cashflows,
            'liability_cashflows': liability_cashflows,
            'surplus': surplus
        }
    
    def _aggregate_results(self, scenario_results: List[Dict]) -> Dict:
        """Aggregate results across scenarios."""
        num_scenarios = len(scenario_results)
        time_steps = len(scenario_results[0]['portfolio_values'])
        
        # Initialize aggregation arrays
        agg_results = {
            'portfolio_values': np.zeros((time_steps, num_scenarios)),
            'liability_values': np.zeros((time_steps, num_scenarios)),
            'surplus': np.zeros((time_steps, num_scenarios)),
            'asset_cashflows': np.zeros((time_steps, num_scenarios)),
            'liability_cashflows': np.zeros((time_steps, num_scenarios))
        }
        
        # Collect results
        for scenario in scenario_results:
            idx = scenario['scenario_idx']
            for key in agg_results:
                agg_results[key][:, idx] = scenario[key]
        
        # Calculate statistics
        stats = {}
        for key in agg_results:
            data = agg_results[key]
            stats[f'{key}_mean'] = np.mean(data, axis=1)
            stats[f'{key}_std'] = np.std(data, axis=1)
            stats[f'{key}_percentile_5'] = np.percentile(data, 5, axis=1)
            stats[f'{key}_percentile_95'] = np.percentile(data, 95, axis=1)
        
        return {
            'scenario_data': agg_results,
            'statistics': stats
        }
    
    def calculate_risk_metrics(self, results: Dict) -> Dict:
        """Calculate key risk metrics from projection results."""
        metrics = {
            'var_95': self._calculate_var(results, 0.95),
            'cte_95': self._calculate_cte(results, 0.95),
            'duration': self._calculate_duration(results),
            'convexity': self._calculate_convexity(results),
            'surplus_volatility': np.std(results['scenario_data']['surplus'], axis=1),
            'funding_ratio': (
                results['statistics']['portfolio_values_mean'] /
                results['statistics']['liability_values_mean']
            ),
            'cash_flow_match_quality': self._calculate_cf_match_quality(
                results['scenario_data']['asset_cashflows'],
                results['scenario_data']['liability_cashflows']
            )
        }
        return metrics
    
    def _calculate_cf_match_quality(self, 
                                  asset_cf: np.ndarray, 
                                  liability_cf: np.ndarray) -> float:
        """Calculate quality of cash flow matching."""
        cf_diff = asset_cf - liability_cf
        return {
            'mean_mismatch': np.mean(np.abs(cf_diff)),
            'max_mismatch': np.max(np.abs(cf_diff)),
            'duration_mismatch': self._calculate_cf_duration(asset_cf) - 
                               self._calculate_cf_duration(liability_cf)
        }
    
    def _calculate_var(self, results: Dict, percentile: float) -> float:
        """Calculate Value at Risk at specified percentile."""
        # Implementation for VaR calculation
        pass
    
    def _calculate_cte(self, results: Dict, percentile: float) -> float:
        """Calculate Conditional Tail Expectation at specified percentile."""
        # Implementation for CTE calculation
        pass
    
    def _calculate_duration(self, results: Dict) -> float:
        """Calculate effective duration of portfolio."""
        # Implementation for duration calculation
        pass
    
    def _calculate_convexity(self, results: Dict) -> float:
        """Calculate convexity of portfolio."""
        # Implementation for convexity calculation
        pass
    
    def _calculate_cf_duration(self, cashflows: np.ndarray) -> float:
        """Calculate duration of cash flows."""
        # Implementation for cash flow duration calculation
        pass
