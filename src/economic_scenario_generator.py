"""
Economic scenario generator for actuarial modeling.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScenarioConfig:
    """Configuration for economic scenario generation."""
    # Interest rate parameters
    short_rate_mean: float
    short_rate_speed: float
    short_rate_vol: float
    term_premium_mean: float
    term_premium_vol: float
    
    # Equity market parameters
    equity_return_mean: float
    equity_vol: float
    jump_intensity: float
    jump_mean: float
    jump_vol: float
    
    # Credit market parameters
    credit_spread_mean: float
    credit_spread_speed: float
    credit_spread_vol: float
    default_intensity: float
    recovery_rate: float
    
    # Inflation parameters
    inflation_mean: float
    inflation_speed: float
    inflation_vol: float
    
    # Correlation matrix
    correlation_matrix: Optional[np.ndarray] = None

class EconomicScenarioGenerator:
    """Generate economic scenarios using various stochastic models."""
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
        
    def generate_yield_curve(self, short_rate: float, term_premium: float, maturities: np.ndarray) -> np.ndarray:
        """Generate full yield curve using short rate and term premium."""
        return short_rate + term_premium * (1 - np.exp(-0.1 * maturities))
    
    def generate_scenarios(self, num_scenarios: int, projection_years: int) -> dict:
        from pydantic import validate_arguments
        
        @validate_arguments
        def validate_inputs(num: int, years: int):
            if num <= 0:
                raise ValueError("Number of scenarios must be a positive integer.")
            if years <= 0:
                raise ValueError("Projection years must be a positive integer.")
        
        validate_inputs(num_scenarios, projection_years)
        
        """Generate comprehensive economic scenarios."""
        time_steps = projection_years * 12  # Monthly steps
        dt = 1.0 / 12  # Monthly time step
        
        # Initialize arrays
        scenarios = {
            'short_rate': np.zeros((time_steps, num_scenarios)),
            'term_premium': np.zeros((time_steps, num_scenarios)),
            'yield_curve': np.zeros((time_steps, num_scenarios, 40)),  # 40 maturities up to 30Y
            'equity_return': np.zeros((time_steps, num_scenarios)),
            'equity_price': np.zeros((time_steps, num_scenarios)),
            'credit_spread': np.zeros((time_steps, num_scenarios)),
            'default_event': np.zeros((time_steps, num_scenarios), dtype=bool),
            'inflation': np.zeros((time_steps, num_scenarios))
        }
        
        # Generate correlated random numbers if correlation matrix is provided
        if self.config.correlation_matrix is not None:
            chol = np.linalg.cholesky(self.config.correlation_matrix)
        else:
            chol = np.eye(4)  # Independent processes
            
        # Generate scenarios using Hull-White, jump-diffusion, and mean-reversion models
        for t in range(1, time_steps):
            # Implementation of stochastic processes
            rand = np.random.multivariate_normal(
                mean=np.zeros(4),
                cov=np.eye(4),
                size=num_scenarios
            ) @ chol.T
            
            # Short rate process (Hull-White)
            scenarios['short_rate'][t] = (
                scenarios['short_rate'][t-1] +
                self.config.short_rate_speed * (self.config.short_rate_mean - scenarios['short_rate'][t-1]) * dt +
                self.config.short_rate_vol * np.sqrt(dt) * rand[:, 0]
            )
            
            # Term premium process
            scenarios['term_premium'][t] = (
                scenarios['term_premium'][t-1] +
                0.2 * (self.config.term_premium_mean - scenarios['term_premium'][t-1]) * dt +
                self.config.term_premium_vol * np.sqrt(dt) * rand[:, 1]
            )
            
            # Generate full yield curve
            maturities = np.linspace(0, 30, 40)  # Maturities up to 30 years
            for scen in range(num_scenarios):
                scenarios['yield_curve'][t, scen] = self.generate_yield_curve(
                    scenarios['short_rate'][t, scen],
                    scenarios['term_premium'][t, scen],
                    maturities
                )
            
            # Other market factors...
            # Equity returns (Merton jump-diffusion)
            scenarios['equity_return'][t] = (
                (self.config.equity_return_mean - 0.5 * self.config.equity_vol**2) * dt +
                self.config.equity_vol * np.sqrt(dt) * rand[:, 2] +
                np.sum(np.random.normal(
                    self.config.jump_mean,
                    self.config.jump_vol,
                    size=np.random.poisson(self.config.jump_intensity * dt)
                ), axis=0)
            )
            
            # Credit spreads (mean-reverting process)
            scenarios['credit_spread'][t] = (
                scenarios['credit_spread'][t-1] +
                self.config.credit_spread_speed * (self.config.credit_spread_mean - scenarios['credit_spread'][t-1]) * dt +
                self.config.credit_spread_vol * np.sqrt(dt) * rand[:, 3]
            )
            
            # Default events (Poisson process)
            scenarios['default_event'][t] = np.random.poisson(self.config.default_intensity * dt) > 0
            
            # Inflation (mean-reverting process)
            scenarios['inflation'][t] = (
                scenarios['inflation'][t-1] +
                self.config.inflation_speed * (self.config.inflation_mean - scenarios['inflation'][t-1]) * dt +
                self.config.inflation_vol * np.sqrt(dt) * rand[:, 0]
            )
        
        return scenarios
