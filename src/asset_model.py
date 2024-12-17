import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import date
from .fixed_income import FixedIncomeModel, Bond
from .public_equity import EquityModel, Equity

class AssetModel:
    """Asset cash flow model with dynamic linking capabilities to liability model."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio = {}
        self.scenarios = None
        self.fixed_income_model = FixedIncomeModel(config.get('fixed_income', {}))
        self.equity_model = EquityModel(config.get('equity', {}))
        
    def set_economic_scenarios(self, scenarios: pd.DataFrame):
        """Set economic scenarios for asset projections."""
        self.scenarios = scenarios
        
    def project_fixed_income(self, bonds: List[Bond], scenario_idx: int) -> pd.DataFrame:
        """Project fixed income cash flows under given scenario."""
        if self.scenarios is None:
            raise ValueError("Economic scenarios must be set before projection")
            
        scenario_rates = self.scenarios.iloc[scenario_idx]
        projection_dates = pd.date_range(
            start=scenario_rates.index[0],
            end=scenario_rates.index[-1],
            freq='M'
        ).date
        
        all_cashflows = []
        
        for bond in bonds:
            cf = self.fixed_income_model.project_cashflows(
                bond,
                projection_dates,
                scenario_rates
            )
            cf['instrument_id'] = bond.id
            all_cashflows.append(cf)
            
        if not all_cashflows:
            return pd.DataFrame()
            
        return pd.concat(all_cashflows, ignore_index=True)
        
    def calculate_portfolio_metrics(self, bonds: List[Bond], yield_curve: pd.Series) -> Dict:
        """Calculate key metrics for the fixed income portfolio."""
        metrics = {
            'total_market_value': 0.0,
            'weighted_duration': 0.0,
            'weighted_convexity': 0.0
        }
        
        total_value = 0
        
        for bond in bonds:
            # Use the yield rate corresponding to the bond's term
            term_to_maturity = (bond.maturity_date - date.today()).days / 365
            yield_rate = np.interp(
                term_to_maturity,
                yield_curve.index,
                yield_curve.values
            )
            
            duration = self.fixed_income_model.calculate_duration(bond, yield_rate)
            convexity = self.fixed_income_model.calculate_convexity(bond, yield_rate)
            
            metrics['total_market_value'] += bond.purchase_price
            metrics['weighted_duration'] += duration * bond.purchase_price
            metrics['weighted_convexity'] += convexity * bond.purchase_price
            total_value += bond.purchase_price
        
        if total_value > 0:
            metrics['weighted_duration'] /= total_value
            metrics['weighted_convexity'] /= total_value
            
        return metrics
        
    def project_equity(self, equities: List[Equity], scenario_idx: int) -> pd.DataFrame:
        """Project equity cash flows including dividends under given scenario."""
        if self.scenarios is None:
            raise ValueError("Economic scenarios must be set before projection")
            
        scenario_data = self.scenarios.iloc[scenario_idx:scenario_idx+1]
        start_date = scenario_data.index[0]
        end_date = start_date + pd.DateOffset(months=59)  # Project for 60 months
        
        projection_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq='ME'
        ).date
        
        # Create scenario rates for the projection period
        scenario_rates = pd.DataFrame({
            'equity_return': [scenario_data['equity_return'].iloc[0]] * len(projection_dates),
            'risk_free_rate': [scenario_data['risk_free_rate'].iloc[0]] * len(projection_dates)
        }, index=projection_dates)
        
        all_cashflows = []
        
        for equity in equities:
            cf = self.equity_model.project_cashflows(
                equity,
                projection_dates,
                scenario_rates
            )
            all_cashflows.append(cf)
            
        if not all_cashflows:
            return pd.DataFrame()
            
        return pd.concat(all_cashflows, ignore_index=True)
        
    def calculate_reinvestment(self, available_cash: float, projection_date: pd.Timestamp,
                             scenario_idx: int) -> Dict:
        """Calculate reinvestment strategy based on available cash."""
        # Implementation for reinvestment logic
        pass
        
    def rebalance_portfolio(self, current_allocation: Dict, target_allocation: Dict,
                          tolerance: float = 0.05) -> Dict:
        """Rebalance portfolio based on target allocation."""
        # Implementation for portfolio rebalancing
        pass
        
    def calculate_key_metrics(self) -> Dict:
        """Calculate key risk metrics for the asset portfolio."""
        # Implementation for risk metrics calculation
        pass
