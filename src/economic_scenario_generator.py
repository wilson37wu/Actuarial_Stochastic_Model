"""
Economic scenario generator for actuarial modeling.
"""
import numpy as np
from dataclasses import dataclass

@dataclass
class ScenarioConfig:
    """Configuration for economic scenario generation."""
    short_rate_mean: float
    short_rate_speed: float
    short_rate_vol: float
    equity_return_mean: float
    equity_vol: float
    jump_intensity: float
    jump_mean: float
    jump_vol: float
    credit_spread_mean: float
    credit_spread_vol: float
    inflation_mean: float
    inflation_vol: float

class EconomicScenarioGenerator:
    """Generate economic scenarios using various stochastic models."""
    
    def __init__(self, config: ScenarioConfig):
        """Initialize the scenario generator with configuration parameters."""
        self.config = config
    
    def generate_scenarios(self, num_scenarios: int, projection_years: int) -> dict:
        """Generate economic scenarios for all factors."""
        time_steps = projection_years + 1  # Include initial values
        dt = 1.0  # Annual time step
        
        scenarios = {
            'short_rate': np.zeros((time_steps, num_scenarios)),
            'long_rate': np.zeros((time_steps, num_scenarios)),
            'equity_return': np.zeros((time_steps, num_scenarios)),
            'credit_spread': np.zeros((time_steps, num_scenarios)),
            'inflation': np.zeros((time_steps, num_scenarios))
        }
        
        # Generate scenarios for each economic factor
        for i in range(num_scenarios):
            # Short rates (Hull-White model)
            short_rates = self._generate_hull_white_rates(time_steps, dt)
            scenarios['short_rate'][:, i] = short_rates
            
            # Long rates (derived from short rates with term premium)
            term_premium = 0.01  # 1% term premium
            scenarios['long_rate'][:, i] = short_rates + term_premium
            
            # Equity returns (Merton jump-diffusion)
            scenarios['equity_return'][:, i] = self._generate_merton_jumps(time_steps, dt)
            
            # Credit spreads (mean-reverting process)
            scenarios['credit_spread'][:, i] = self._generate_credit_spreads(time_steps, dt)
            
            # Inflation (mean-reverting process)
            scenarios['inflation'][:, i] = self._generate_inflation(time_steps, dt)
        
        return scenarios
    
    def _generate_hull_white_rates(self, time_steps: int, dt: float) -> np.ndarray:
        """Generate interest rates using Hull-White model."""
        rates = np.zeros(time_steps)
        rates[0] = self.config.short_rate_mean
        
        for t in range(1, time_steps):
            drift = self.config.short_rate_speed * (self.config.short_rate_mean - rates[t-1])
            diffusion = self.config.short_rate_vol * np.random.normal()
            rates[t] = rates[t-1] + drift * dt + diffusion * np.sqrt(dt)
        
        return np.maximum(rates, 0.0)  # Ensure non-negative rates
    
    def _generate_merton_jumps(self, time_steps: int, dt: float) -> np.ndarray:
        """Generate equity returns using Merton jump-diffusion model."""
        returns = np.zeros(time_steps)
        returns[0] = 0.0  # Initial return
        
        for t in range(1, time_steps):
            # Diffusion component
            diffusion = (self.config.equity_return_mean - 0.5 * self.config.equity_vol**2) * dt + \
                       self.config.equity_vol * np.random.normal() * np.sqrt(dt)
            
            # Jump component
            num_jumps = np.random.poisson(self.config.jump_intensity * dt)
            jumps = np.sum(np.random.normal(
                self.config.jump_mean,
                self.config.jump_vol,
                size=num_jumps
            )) if num_jumps > 0 else 0
            
            returns[t] = diffusion + jumps
        
        return returns
    
    def _generate_credit_spreads(self, time_steps: int, dt: float) -> np.ndarray:
        """Generate credit spreads using mean-reverting process."""
        spreads = np.zeros(time_steps)
        spreads[0] = self.config.credit_spread_mean
        
        for t in range(1, time_steps):
            drift = 0.5 * (self.config.credit_spread_mean - spreads[t-1])
            diffusion = self.config.credit_spread_vol * np.random.normal()
            spreads[t] = spreads[t-1] + drift * dt + diffusion * np.sqrt(dt)
        
        return np.maximum(spreads, 0.0)  # Ensure non-negative spreads
    
    def _generate_inflation(self, time_steps: int, dt: float) -> np.ndarray:
        """Generate inflation rates using mean-reverting process."""
        inflation = np.zeros(time_steps)
        inflation[0] = self.config.inflation_mean
        
        for t in range(1, time_steps):
            drift = 0.3 * (self.config.inflation_mean - inflation[t-1])
            diffusion = self.config.inflation_vol * np.random.normal()
            inflation[t] = inflation[t-1] + drift * dt + diffusion * np.sqrt(dt)
        
        return inflation
