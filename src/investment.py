"""
Module for investment strategies and asset modeling.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .enums import AssetClass

@dataclass
class AssetParameters:
    """Parameters for asset return modeling."""
    expected_return: float
    volatility: float
    correlation: Dict[str, float] = None  # Correlation with other assets
    credit_spread: Optional[float] = None  # For fixed income
    duration: Optional[float] = None      # For fixed income
    dividend_yield: Optional[float] = None # For equity

class InvestmentPortfolio:
    """Represents an investment portfolio with multiple asset classes."""
    
    def __init__(self, 
                 initial_allocation: Dict[AssetClass, float],
                 asset_params: Dict[AssetClass, AssetParameters]):
        """Initialize portfolio with allocations and parameters."""
        self.validate_allocation(initial_allocation)
        self.allocation = initial_allocation
        self.asset_params = asset_params
        self.rebalancing_threshold = 0.05  # 5% threshold
        
        # Initialize tracking
        self.market_values: Dict[date, Dict[AssetClass, float]] = {}
        self.returns: Dict[date, Dict[AssetClass, float]] = {}
        self.transactions: Dict[date, List[Tuple[AssetClass, float, str]]] = {}
    
    @staticmethod
    def validate_allocation(allocation: Dict[AssetClass, float]):
        """Validate that allocations sum to 1."""
        total = sum(allocation.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Allocations must sum to 1, got {total}")
    
    def rebalance(self, date: date):
        """Rebalance portfolio if any asset is outside threshold."""
        current_values = self.market_values[date]
        total_value = sum(current_values.values())
        
        # Calculate current allocations
        current_alloc = {
            asset: value / total_value 
            for asset, value in current_values.items()
        }
        
        # Check if rebalancing is needed
        need_rebalance = any(
            abs(curr - target) > self.rebalancing_threshold
            for asset, curr in current_alloc.items()
            for target in [self.allocation[asset]]
        )
        
        if need_rebalance:
            transactions = []
            for asset in current_values:
                target_value = total_value * self.allocation[asset]
                current_value = current_values[asset]
                trade = target_value - current_value
                
                if abs(trade) > 0.01:  # Minimum trade size
                    transactions.append(
                        (asset, abs(trade), "BUY" if trade > 0 else "SELL")
                    )
                    current_values[asset] = target_value
            
            self.transactions[date] = transactions

    def update_allocation(self, new_allocation: Dict[AssetClass, float]) -> None:
        """Update portfolio allocation.
        
        Args:
            new_allocation: New target allocation for each asset class
        """
        self.validate_allocation(new_allocation)
        self.allocation = new_allocation
        
        # Record the rebalancing transaction
        if hasattr(self, 'transactions'):
            current_date = date.today()
            self.transactions[current_date] = [
                (asset, alloc, 'rebalance')
                for asset, alloc in new_allocation.items()
            ]

    def generate_scenarios(self, n_scenarios: int, n_periods: int, seed: Optional[int] = None) -> pd.DataFrame:
        """Generate return scenarios for the portfolio.
        
        Args:
            n_scenarios: Number of scenarios to generate
            n_periods: Number of periods to project
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with scenarios as columns and periods as rows
        """
        if seed is not None:
            np.random.seed(seed)
            
        # Create correlation matrix
        assets = list(self.allocation.keys())
        n_assets = len(assets)
        correlation = np.eye(n_assets)  # Default to identity matrix
        
        # Create arrays for means and volatilities
        means = np.array([self.asset_params[asset].expected_return / 12 for asset in assets])
        vols = np.array([self.asset_params[asset].volatility / np.sqrt(12) for asset in assets])
        
        # Create covariance matrix
        cov_matrix = np.outer(vols, vols) * correlation
        
        # Generate correlated normal random variables
        Z = np.random.multivariate_normal(
            mean=np.zeros(n_assets),
            cov=cov_matrix,
            size=(n_periods, n_scenarios)
        )
        
        # Convert to returns using geometric Brownian motion
        returns = np.exp(
            (means - 0.5 * vols**2).reshape(1, -1, 1) + 
            Z.reshape(n_periods, n_assets, n_scenarios)
        ) - 1
        
        # Calculate portfolio returns
        weights = np.array([self.allocation[asset] for asset in assets])
        portfolio_returns = np.sum(
            returns * weights.reshape(1, -1, 1),
            axis=1
        )
        
        # Create DataFrame
        scenarios_df = pd.DataFrame(
            portfolio_returns,
            columns=[f'Scenario_{i+1}' for i in range(n_scenarios)]
        )
        scenarios_df.index = range(1, n_periods + 1)
        
        return scenarios_df

    def get_portfolio_metrics(self) -> Dict[str, float]:
        """Calculate portfolio metrics.
        
        Returns:
            Dictionary with portfolio metrics
        """
        # Calculate expected return (annualized)
        portfolio_return = sum(
            self.allocation[asset] * self.asset_params[asset].expected_return
            for asset in self.allocation
        )
        
        # Calculate portfolio volatility (annualized)
        assets = list(self.allocation.keys())
        n_assets = len(assets)
        correlation = np.eye(n_assets)  # Default to identity matrix
        
        weights = np.array([self.allocation[asset] for asset in assets])
        vols = np.array([self.asset_params[asset].volatility for asset in assets])
        cov_matrix = np.outer(vols, vols) * correlation
        
        portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
        
        # Calculate Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol
        
        return {
            'expected_return': portfolio_return,
            'volatility': portfolio_vol,
            'sharpe_ratio': sharpe_ratio
        }

    def calculate_expected_return(self) -> float:
        """Calculate portfolio expected return based on current allocation."""
        return sum(
            alloc * self.asset_params[asset].expected_return
            for asset, alloc in self.allocation.items()
        )
    
    def calculate_volatility(self) -> float:
        """Calculate portfolio volatility based on current allocation."""
        # Simple volatility calculation without correlations
        return np.sqrt(sum(
            alloc * alloc * self.asset_params[asset].volatility ** 2
            for asset, alloc in self.allocation.items()
        ))
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate portfolio Sharpe ratio."""
        excess_return = self.calculate_expected_return() - risk_free_rate
        volatility = self.calculate_volatility()
        return excess_return / volatility if volatility > 0 else 0
    
    def calculate_var(self, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk at given confidence level."""
        portfolio_return = self.calculate_expected_return()
        portfolio_vol = self.calculate_volatility()
        z_score = np.percentile(np.random.standard_normal(10000), (1 - confidence_level) * 100)
        return -(portfolio_return + z_score * portfolio_vol)

class TargetDateStrategy:
    """Target date investment strategy."""
    
    def __init__(self, 
                 target_year: int,
                 initial_equity: float = 0.9,
                 final_equity: float = 0.3):
        """Initialize target date strategy."""
        self.target_year = target_year
        self.initial_equity = initial_equity
        self.final_equity = final_equity
        
        # Define glide path
        years_to_target = max(0, target_year - date.today().year)
        self.years_to_retirement = years_to_target
        
        # Initialize conservative allocation
        self.conservative = {
            AssetClass.CASH: 0.05,
            AssetClass.MONEY_MARKET: 0.10,
            AssetClass.GOVERNMENT_BOND: 0.35,
            AssetClass.CORPORATE_BOND: 0.20,
            AssetClass.LARGE_CAP_EQUITY: 0.20,
            AssetClass.INTERNATIONAL_EQUITY: 0.10
        }
        
        # Initialize aggressive allocation
        self.aggressive = {
            AssetClass.CASH: 0.02,
            AssetClass.MONEY_MARKET: 0.03,
            AssetClass.GOVERNMENT_BOND: 0.05,
            AssetClass.CORPORATE_BOND: 0.10,
            AssetClass.LARGE_CAP_EQUITY: 0.40,
            AssetClass.SMALL_CAP_EQUITY: 0.15,
            AssetClass.INTERNATIONAL_EQUITY: 0.15,
            AssetClass.EMERGING_MARKETS: 0.10
        }
    
    def get_allocation(self, current_date: date) -> Dict[AssetClass, float]:
        """Get target allocation based on current date."""
        years_remaining = max(0, self.target_year - current_date.year)
        equity_weight = self._calculate_equity_weight(years_remaining)
        
        # Interpolate between conservative and aggressive allocations
        allocation = {}
        all_assets = set(self.conservative.keys()) | set(self.aggressive.keys())
        
        for asset in all_assets:
            conservative_alloc = self.conservative.get(asset, 0.0)
            aggressive_alloc = self.aggressive.get(asset, 0.0)
            allocation[asset] = (
                conservative_alloc * (1 - equity_weight) +
                aggressive_alloc * equity_weight
            )
        
        return allocation
    
    def _calculate_equity_weight(self, years_remaining: int) -> float:
        """Calculate equity weight based on years to target date."""
        if years_remaining >= self.years_to_retirement:
            return self.initial_equity
        elif years_remaining <= 0:
            return self.final_equity
        else:
            # Linear interpolation
            progress = years_remaining / self.years_to_retirement
            return self.final_equity + (
                self.initial_equity - self.final_equity
            ) * progress

class DynamicStrategy:
    """Dynamic investment strategy based on market conditions."""
    
    def __init__(self,
                 base_allocation: Dict[AssetClass, float],
                 max_deviation: float = 0.2):
        """Initialize dynamic strategy."""
        self.base_allocation = base_allocation
        self.max_deviation = max_deviation
        self.market_indicators = {
            'momentum': 0.0,    # Price momentum
            'volatility': 0.0,  # Market volatility
            'yield_curve': 0.0, # Yield curve slope
            'valuation': 0.0    # Market valuation metrics
        }
    
    def update_indicators(self,
                        momentum: float,
                        volatility: float,
                        yield_curve: float,
                        valuation: float):
        """Update market indicators."""
        self.market_indicators.update({
            'momentum': momentum,
            'volatility': volatility,
            'yield_curve': yield_curve,
            'valuation': valuation
        })
    
    def get_allocation(self) -> Dict[AssetClass, float]:
        """Get dynamic allocation based on market indicators."""
        # Calculate composite signal (-1 to 1)
        signal = (
            0.3 * self.market_indicators['momentum'] +
            -0.3 * self.market_indicators['volatility'] +
            0.2 * self.market_indicators['yield_curve'] +
            0.2 * self.market_indicators['valuation']
        )
        
        # Adjust allocations
        allocation = {}
        risk_assets = {
            AssetClass.LARGE_CAP_EQUITY,
            AssetClass.SMALL_CAP_EQUITY,
            AssetClass.INTERNATIONAL_EQUITY,
            AssetClass.EMERGING_MARKETS,
            AssetClass.HIGH_YIELD_BOND
        }
        
        safe_assets = {
            AssetClass.CASH,
            AssetClass.MONEY_MARKET,
            AssetClass.GOVERNMENT_BOND
        }
        
        for asset, base_alloc in self.base_allocation.items():
            if asset in risk_assets:
                # Increase risk assets when signal is positive
                adjustment = self.max_deviation * signal
            elif asset in safe_assets:
                # Decrease safe assets when signal is positive
                adjustment = -self.max_deviation * signal
            else:
                adjustment = 0.0
            
            allocation[asset] = max(0.0, min(1.0, base_alloc + adjustment))
        
        # Normalize allocations to sum to 1
        total = sum(allocation.values())
        return {k: v/total for k, v in allocation.items()}
