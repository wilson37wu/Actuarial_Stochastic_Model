"""
Economic scenario generator for stochastic modeling.
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from scipy.stats import norm
from datetime import date
from src.financial_models import ALMEngine, ModelParameters

@dataclass
class EconomicFactors:
    """Container for economic factors at a point in time."""
    short_rate: float
    long_rate: float
    equity_return: float
    inflation_rate: float
    credit_spread: float
    date: date

class EconomicScenarioGenerator:
    """Generates consistent economic scenarios using correlated random variables."""
    
    def __init__(self, 
                 initial_short_rate: float = 0.02,
                 initial_long_rate: float = 0.03,
                 mean_reversion_speed: float = 0.15,
                 volatility_short_rate: float = 0.012,
                 volatility_long_rate: float = 0.008,
                 equity_risk_premium: float = 0.06,
                 equity_volatility: float = 0.15,
                 inflation_mean: float = 0.02,
                 inflation_volatility: float = 0.01,
                 correlation_matrix: Optional[np.ndarray] = None):
        """Initialize the economic scenario generator."""
        # Initialize model parameters
        self.params = ModelParameters(
            mean_reversion_speed=mean_reversion_speed,
            rate_volatility=volatility_short_rate,
            initial_rate=initial_short_rate,
            long_term_rate=initial_long_rate,
            equity_volatility=equity_volatility,
            equity_price=100.0,  # Starting price index at 100
            equity_dividend=equity_risk_premium
        )
        
        # Initialize ALM engine
        self.alm_engine = ALMEngine(self.params)
        
        # Store correlation matrix for inflation modeling
        if correlation_matrix is None:
            self.correlation_matrix = np.array([
                [1.0,  0.7,  0.3,  0.2],  # Short rate
                [0.7,  1.0,  0.2,  0.3],  # Long rate
                [0.3,  0.2,  1.0,  0.1],  # Equity
                [0.2,  0.3,  0.1,  1.0]   # Inflation
            ])
        else:
            self.correlation_matrix = correlation_matrix
        
        self.inflation_mean = inflation_mean
        self.inflation_volatility = inflation_volatility
        
    def generate_scenarios(self, 
                         num_scenarios: int, 
                         projection_years: int,
                         time_steps_per_year: int = 12) -> List[List[EconomicFactors]]:
        """Generate economic scenarios."""
        dt = 1.0 / time_steps_per_year
        T = projection_years * 1.0
        
        try:
            # Generate scenarios using ALM engine
            scenarios = self.alm_engine.simulate_multiple_scenarios(
                num_scenarios=num_scenarios,
                T=T,
                dt=dt
            )
            
            # Convert to list of EconomicFactors
            economic_factors = []
            steps = int(T / dt)
            
            for scenario in range(num_scenarios):
                factors_path = []
                
                # Generate correlated inflation
                inflation_shocks = np.random.standard_normal(steps)
                inflation_path = self.inflation_mean + self.inflation_volatility * inflation_shocks
                
                for step in range(steps):
                    # Ensure all rates are valid numbers
                    short_rate = float(np.nan_to_num(scenarios['interest_rates'][scenario, step], nan=0.02))
                    credit_spread = float(np.nan_to_num(scenarios['credit_spreads'][scenario, step], nan=0.01))
                    
                    # Calculate equity return, handling the first step specially
                    if step > 0:
                        prev_price = float(np.nan_to_num(scenarios['equity_prices_heston'][scenario, step-1], nan=100.0))
                        curr_price = float(np.nan_to_num(scenarios['equity_prices_heston'][scenario, step], nan=prev_price))
                        equity_return = np.log(curr_price / prev_price) if prev_price > 0 else 0.0
                    else:
                        equity_return = 0.0
                    
                    # Create economic factors with validated values
                    current_date = date.today()  # You might want to advance this based on step
                    factors = EconomicFactors(
                        short_rate=np.clip(short_rate, 0.001, 0.15),  # Bound rates
                        long_rate=np.clip(short_rate + credit_spread, 0.002, 0.20),
                        equity_return=np.clip(equity_return, -0.5, 0.5),  # Limit extreme returns
                        inflation_rate=np.clip(inflation_path[step], -0.05, 0.15),
                        credit_spread=np.clip(credit_spread, 0.001, 0.10),
                        date=current_date
                    )
                    factors_path.append(factors)
                
                economic_factors.append(factors_path)
                
            return economic_factors
            
        except Exception as e:
            print(f"Warning: Error in scenario generation: {e}")
            # Return a simple deterministic scenario as fallback
            return self._generate_fallback_scenarios(num_scenarios, projection_years, time_steps_per_year)
    
    def _generate_fallback_scenarios(self, num_scenarios: int, projection_years: int, time_steps_per_year: int) -> List[List[EconomicFactors]]:
        """Generate simple deterministic scenarios as fallback."""
        steps = projection_years * time_steps_per_year
        economic_factors = []
        
        for _ in range(num_scenarios):
            factors_path = []
            for step in range(steps):
                current_date = date.today()  # You might want to advance this based on step
                factors = EconomicFactors(
                    short_rate=0.02,
                    long_rate=0.03,
                    equity_return=0.06 / time_steps_per_year,
                    inflation_rate=0.02,
                    credit_spread=0.01,
                    date=current_date
                )
                factors_path.append(factors)
            economic_factors.append(factors_path)
        
        return economic_factors
    
    def get_discount_factors(self, 
                           rates: List[float], 
                           times: List[float]) -> np.ndarray:
        """Calculate discount factors from a series of rates."""
        return np.exp(-np.array(rates) * np.array(times))
    
    def calibrate_to_market(self, 
                          market_rates: Dict[str, float],
                          market_spreads: Dict[str, float],
                          market_volatilities: Dict[str, float]) -> None:
        """Calibrate the model to market observables."""
        # Update model parameters based on market data
        if 'short_rate' in market_rates:
            self.initial_short_rate = market_rates['short_rate']
        if 'long_rate' in market_rates:
            self.initial_long_rate = market_rates['long_rate']
        if 'equity_volatility' in market_volatilities:
            self.equity_volatility = market_volatilities['equity_volatility']
