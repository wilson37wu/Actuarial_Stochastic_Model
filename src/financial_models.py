"""
Advanced financial models for ALM engine.
"""
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class ModelParameters:
    """Parameters for financial models."""
    # Interest rate model parameters
    mean_reversion_speed: float = 0.1
    rate_volatility: float = 0.02
    initial_rate: float = 0.03
    long_term_rate: float = 0.04
    
    # Credit model parameters
    credit_intensity: float = 0.02
    asset_value: float = 100.0
    asset_volatility: float = 0.2
    debt_value: float = 80.0
    
    # Equity model parameters
    equity_volatility: float = 0.15
    equity_price: float = 100.0
    equity_dividend: float = 0.02
    
    # Heston model parameters
    variance_reversion_speed: float = 2.0
    long_run_variance: float = 0.04
    variance_volatility: float = 0.3
    price_variance_correlation: float = -0.7
    initial_variance: float = 0.04
    
    # Jump diffusion parameters
    jump_intensity: float = 0.1
    jump_mean: float = -0.2
    jump_std: float = 0.2

class HullWhiteModel:
    """Hull-White one-factor interest rate model."""
    def __init__(self, a: float, sigma: float):
        self.a = a  # Speed of mean reversion
        self.sigma = sigma  # Volatility

    def simulate(self, r0: float, theta: float, T: float, dt: float) -> np.ndarray:
        """Simulate short rate dynamics."""
        steps = int(T / dt)
        rates = np.zeros(steps)
        rates[0] = r0
        for t in range(1, steps):
            dr = (theta - self.a * rates[t - 1]) * dt + self.sigma * np.sqrt(dt) * np.random.normal()
            rates[t] = rates[t - 1] + dr
        return rates

class JarrowTurnbullModel:
    """Jarrow-Turnbull reduced-form credit model."""
    def __init__(self, intensity: float):
        self.intensity = intensity

    def price(self, face_value: float, T: float, r: float) -> float:
        """Price a defaultable bond."""
        return face_value * np.exp(-(r + self.intensity) * T)

    def survival_probability(self, T: float) -> float:
        """Calculate survival probability."""
        return np.exp(-self.intensity * T)

class MertonCreditModel:
    """Merton structural credit model."""
    def __init__(self, asset_value: float, asset_volatility: float, debt: float, r: float):
        self.asset_value = asset_value
        self.asset_volatility = asset_volatility
        self.debt = debt
        self.r = r

    def credit_spread(self, T: float) -> float:
        """Calculate credit spread."""
        if T <= 0:
            return 0.0
        d1 = (np.log(self.asset_value / self.debt) + (self.r + 0.5 * self.asset_volatility**2) * T) / (self.asset_volatility * np.sqrt(T))
        d2 = d1 - self.asset_volatility * np.sqrt(T)
        survival_prob = norm.cdf(d2)
        # Add small constant to avoid division by zero
        survival_prob = max(survival_prob, 1e-10)
        return -np.log(survival_prob) / T

    def default_probability(self, T: float) -> float:
        """Calculate probability of default."""
        d2 = (np.log(self.asset_value / self.debt) + (self.r - 0.5 * self.asset_volatility**2) * T) / (self.asset_volatility * np.sqrt(T))
        return norm.cdf(-d2)

class HestonModel:
    """Heston stochastic volatility model."""
    def __init__(self, S0: float, v0: float, kappa: float, theta: float, xi: float, rho: float):
        self.S0 = S0
        self.v0 = v0
        self.kappa = kappa  # Mean reversion speed of variance
        self.theta = theta  # Long-run variance
        self.xi = xi  # Volatility of variance
        self.rho = rho  # Correlation between asset and variance

    def simulate(self, T: float, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate price and volatility paths."""
        steps = int(T / dt)
        prices = np.zeros(steps)
        variances = np.zeros(steps)
        prices[0] = self.S0
        variances[0] = self.v0

        for t in range(1, steps):
            dw1 = np.random.normal() * np.sqrt(dt)
            dw2 = self.rho * dw1 + np.sqrt(1 - self.rho**2) * np.random.normal() * np.sqrt(dt)

            variances[t] = max(0, variances[t - 1] + self.kappa * (self.theta - variances[t - 1]) * dt + self.xi * np.sqrt(variances[t - 1]) * dw2)
            prices[t] = prices[t - 1] * np.exp(-0.5 * variances[t - 1] * dt + np.sqrt(variances[t - 1]) * dw1)

        return prices, variances

class MertonJumpDiffusionModel:
    """Merton jump-diffusion model."""
    def __init__(self, S0: float, sigma: float, r: float, jump_intensity: float, jump_mean: float, jump_std: float):
        self.S0 = S0
        self.sigma = sigma
        self.r = r
        self.jump_intensity = jump_intensity
        self.jump_mean = jump_mean
        self.jump_std = jump_std

    def simulate(self, T: float, dt: float) -> np.ndarray:
        """Simulate price path."""
        steps = int(T / dt)
        prices = np.zeros(steps)
        prices[0] = self.S0

        for t in range(1, steps):
            jump = np.random.poisson(self.jump_intensity * dt)
            jump_size = np.exp(np.random.normal(self.jump_mean, self.jump_std)) if jump > 0 else 1

            dS = self.r * prices[t - 1] * dt + self.sigma * prices[t - 1] * np.random.normal() * np.sqrt(dt)
            prices[t] = prices[t - 1] + dS * jump_size

        return prices

class ALMEngine:
    """Asset-Liability Management Engine."""
    def __init__(self, params: ModelParameters):
        self.params = params
        
        # Initialize models
        self.interest_rate_model = HullWhiteModel(
            a=params.mean_reversion_speed,
            sigma=params.rate_volatility
        )
        
        self.credit_model = MertonCreditModel(
            asset_value=params.asset_value,
            asset_volatility=params.asset_volatility,
            debt=params.debt_value,
            r=params.initial_rate
        )
        
        self.equity_model = HestonModel(
            S0=params.equity_price,
            v0=params.initial_variance,
            kappa=params.variance_reversion_speed,
            theta=params.long_run_variance,
            xi=params.variance_volatility,
            rho=params.price_variance_correlation
        )
        
        self.jump_model = MertonJumpDiffusionModel(
            S0=params.equity_price,
            sigma=params.equity_volatility,
            r=params.initial_rate,
            jump_intensity=params.jump_intensity,
            jump_mean=params.jump_mean,
            jump_std=params.jump_std
        )
    
    def simulate_scenario(self, T: float, dt: float) -> Dict[str, np.ndarray]:
        """Simulate a complete economic scenario."""
        # Simulate interest rates
        rates = self.interest_rate_model.simulate(
            r0=self.params.initial_rate,
            theta=self.params.long_term_rate,
            T=T,
            dt=dt
        )
        
        # Simulate equity prices with both Heston and Jump models
        heston_prices, variances = self.equity_model.simulate(T, dt)
        jump_prices = self.jump_model.simulate(T, dt)
        
        # Calculate credit spreads through time
        steps = int(T / dt)
        credit_spreads = np.array([
            self.credit_model.credit_spread(t * dt)
            for t in range(steps)
        ])
        
        return {
            'interest_rates': rates,
            'credit_spreads': credit_spreads,
            'equity_prices_heston': heston_prices,
            'equity_prices_jump': jump_prices,
            'equity_variances': variances
        }
    
    def simulate_multiple_scenarios(self, 
                                 num_scenarios: int,
                                 T: float,
                                 dt: float) -> Dict[str, np.ndarray]:
        """Simulate multiple economic scenarios."""
        scenarios = []
        for _ in range(num_scenarios):
            scenario = self.simulate_scenario(T, dt)
            scenarios.append(scenario)
            
        # Convert to arrays
        combined = {}
        for key in scenarios[0].keys():
            combined[key] = np.array([s[key] for s in scenarios])
            
        return combined
