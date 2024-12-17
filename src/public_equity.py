import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, date

@dataclass
class Equity:
    """Represents a public equity position."""
    id: str
    quantity: float
    initial_price: float
    dividend_yield: float
    beta: float
    sector: str
    purchase_date: date
    currency: str = 'USD'

class EquityModel:
    """Public Equity projection model."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.market_volatility = config.get('market_volatility', 0.15)
        self.sector_correlations = self._load_sector_correlations()
        
    def _load_sector_correlations(self) -> pd.DataFrame:
        """Load sector correlation matrix."""
        # Example correlation matrix (should be loaded from config in practice)
        sectors = ['Technology', 'Financial', 'Healthcare', 'Consumer', 'Industrial']
        return pd.DataFrame(np.eye(len(sectors)), index=sectors, columns=sectors)
        
    def project_cashflows(
        self,
        equity: Equity,
        projection_dates: List[date],
        scenario_rates: pd.DataFrame
    ) -> pd.DataFrame:
        """Project equity cash flows including dividends under given scenario.
        
        Args:
            equity: Equity position to project
            projection_dates: List of dates to project for
            scenario_rates: DataFrame containing market returns and risk-free rates
            
        Returns:
            DataFrame with projected values and cash flows
        """
        # Extract market parameters
        market_returns = scenario_rates['equity_return'].values
        risk_free_rates = scenario_rates['risk_free_rate'].values
        
        # Calculate equity-specific parameters
        equity_volatility = self.market_volatility * np.sqrt(equity.beta)
        equity_drift = risk_free_rates + equity.beta * (market_returns - risk_free_rates)
        
        # Generate monthly price paths using GBM
        dt = 1/12  # monthly time step
        num_steps = len(projection_dates)
        Z = np.random.normal(0, 1, num_steps)
        
        price_path = np.zeros(num_steps)
        price_path[0] = equity.initial_price
        
        for t in range(1, num_steps):
            price_path[t] = price_path[t-1] * np.exp(
                (equity_drift[t] - 0.5 * equity_volatility**2) * dt +
                equity_volatility * np.sqrt(dt) * Z[t]
            )
        
        # Calculate dividends (monthly)
        monthly_div_yield = (1 + equity.dividend_yield)**(1/12) - 1
        dividend_amounts = price_path * monthly_div_yield * equity.quantity
        
        return pd.DataFrame({
            'date': projection_dates,
            'instrument_id': equity.id,
            'market_value': price_path * equity.quantity,
            'dividend_amount': dividend_amounts,
            'total_return': (price_path / price_path[0] - 1) + 
                          np.cumsum(dividend_amounts) / (price_path[0] * equity.quantity)
        })
    
    def calculate_portfolio_metrics(
        self,
        equities: List[Equity],
        market_prices: pd.Series
    ) -> Dict:
        """Calculate key metrics for the equity portfolio."""
        metrics = {
            'total_market_value': 0.0,
            'weighted_beta': 0.0,
            'dividend_yield': 0.0,
            'sector_exposure': {}
        }
        
        total_value = 0
        
        for equity in equities:
            current_price = market_prices.get(equity.id, equity.initial_price)
            market_value = current_price * equity.quantity
            
            metrics['total_market_value'] += market_value
            metrics['weighted_beta'] += equity.beta * market_value
            metrics['dividend_yield'] += equity.dividend_yield * market_value
            
            # Track sector exposure
            metrics['sector_exposure'][equity.sector] = metrics['sector_exposure'].get(
                equity.sector, 0) + market_value
            
            total_value += market_value
        
        if total_value > 0:
            metrics['weighted_beta'] /= total_value
            metrics['dividend_yield'] /= total_value
            
            # Convert sector exposure to percentages
            metrics['sector_exposure'] = {
                sector: value / total_value 
                for sector, value in metrics['sector_exposure'].items()
            }
            
        return metrics
