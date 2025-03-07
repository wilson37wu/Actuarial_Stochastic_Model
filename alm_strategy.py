"""
Asset Liability Management (ALM) Strategy Implementation

This module implements the core ALM strategy functionality for managing assets in relation to liabilities.
It provides tools for monitoring and managing funding ratios, duration gaps, and liquidity requirements.

Key Features:
- Liability cash flow tracking and projection
- Asset-liability matching analysis
- Risk metrics calculation and monitoring
- Stress testing capabilities
- Portfolio optimization framework

Example:
    >>> strategy = ALMStrategy(initial_assets=1000000)
    >>> strategy.add_liability_cashflow(
    ...     time_period=1,
    ...     expected_amount=50000,
    ...     uncertainty=0.05,
    ...     discounted_value=48000
    ... )
    >>> rebalancing_needs = strategy.assess_rebalancing_needs()
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional
from scipy.stats import norm

@dataclass
class LiabilityCashFlow:
    """
    Represents a single liability cash flow with timing and uncertainty information.
    
    Attributes:
        time_period (int): Time period when the cash flow occurs
        expected_amount (float): Expected nominal amount of the cash flow
        uncertainty (float): Measure of uncertainty in the cash flow (e.g., standard deviation)
        discounted_value (float): Present value of the cash flow
    """
    time_period: int
    expected_amount: float
    uncertainty: float
    discounted_value: float

@dataclass
class AssetCashFlow:
    """
    Represents a single asset cash flow with duration and credit quality information.
    
    Attributes:
        time_period (int): Time period when the cash flow occurs
        expected_amount (float): Expected nominal amount of the cash flow
        duration (float): Duration contribution of this cash flow
        credit_quality (str): Credit rating or quality indicator
    """
    time_period: int
    expected_amount: float
    duration: float
    credit_quality: str

class ALMStrategy:
    """
    Implements the core Asset-Liability Management strategy.
    
    This class provides methods for managing and analyzing the relationship between
    assets and liabilities, including risk metrics, stress testing, and optimization.
    
    Attributes:
        initial_assets (float): Initial market value of assets
        target_funding_ratio (float): Target ratio of assets to liabilities
        max_duration_gap (float): Maximum allowed duration mismatch
        min_liquidity_ratio (float): Minimum required liquidity ratio
        liability_cashflows (List[LiabilityCashFlow]): List of liability cash flows
        asset_cashflows (List[AssetCashFlow]): List of asset cash flows
    """
    
    def __init__(self, 
                 initial_assets: float,
                 target_funding_ratio: float = 1.05,
                 max_duration_gap: float = 1.0,
                 min_liquidity_ratio: float = 0.15):
        """
        Initialize the ALM strategy with initial parameters.
        
        Args:
            initial_assets: Starting market value of assets
            target_funding_ratio: Target ratio of assets to liabilities (default: 1.05)
            max_duration_gap: Maximum allowed duration mismatch (default: 1.0)
            min_liquidity_ratio: Minimum required liquidity ratio (default: 0.15)
        """
        self.initial_assets = initial_assets
        self.target_funding_ratio = target_funding_ratio
        self.max_duration_gap = max_duration_gap
        self.min_liquidity_ratio = min_liquidity_ratio
        self.liability_cashflows: List[LiabilityCashFlow] = []
        self.asset_cashflows: List[AssetCashFlow] = []

    def calculate_funding_ratio(self) -> float:
        """
        Calculate the current funding ratio (assets/liabilities).
        
        Returns:
            float: Current funding ratio, or infinity if no liabilities
        """
        total_assets = self.calculate_present_value_assets()
        total_liabilities = self.calculate_present_value_liabilities()
        return total_assets / total_liabilities if total_liabilities > 0 else float('inf')

    def calculate_duration_gap(self) -> float:
        """
        Calculate the duration gap between assets and liabilities.
        
        Returns:
            float: Duration gap (asset duration - liability duration)
        """
        asset_duration = self.calculate_asset_duration()
        liability_duration = self.calculate_liability_duration()
        return asset_duration - liability_duration

    def calculate_cash_flow_matching_ratio(self, time_period: int) -> float:
        """
        Calculate the cash flow matching ratio for a specific time period.
        
        Args:
            time_period: The time period to analyze
            
        Returns:
            float: Ratio of asset cash flows to liability cash flows
        """
        asset_cf = sum(acf.expected_amount for acf in self.asset_cashflows 
                      if acf.time_period == time_period)
        liability_cf = sum(lcf.expected_amount for lcf in self.liability_cashflows 
                         if lcf.time_period == time_period)
        return asset_cf / liability_cf if liability_cf > 0 else float('inf')

    def assess_rebalancing_needs(self) -> Dict[str, bool]:
        """
        Assess whether rebalancing is needed based on various metrics.
        
        Returns:
            Dict[str, bool]: Dictionary indicating which thresholds have been breached
        """
        current_funding_ratio = self.calculate_funding_ratio()
        current_duration_gap = self.calculate_duration_gap()
        
        return {
            "funding_ratio_breach": abs(current_funding_ratio - self.target_funding_ratio) > 0.05,
            "duration_gap_breach": abs(current_duration_gap) > self.max_duration_gap,
            "liquidity_breach": self.calculate_liquidity_ratio() < self.min_liquidity_ratio
        }

    def calculate_surplus_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calculate the Surplus at Risk (SaR) metric.
        
        Args:
            confidence_level: Statistical confidence level (default: 0.95)
            
        Returns:
            float: Surplus at Risk value
        """
        asset_volatility = self.estimate_asset_volatility()
        liability_volatility = self.estimate_liability_volatility()
        correlation = self.estimate_asset_liability_correlation()
        
        surplus_volatility = np.sqrt(
            asset_volatility**2 + liability_volatility**2 - 
            2 * correlation * asset_volatility * liability_volatility
        )
        
        z_score = norm.ppf(confidence_level)
        return z_score * surplus_volatility

    def run_stress_test(self, 
                       interest_rate_shock: float,
                       credit_spread_shock: float,
                       inflation_shock: float) -> Dict[str, float]:
        """
        Run stress tests on the portfolio under various shock scenarios.
        
        Args:
            interest_rate_shock: Parallel shift in interest rates
            credit_spread_shock: Widening of credit spreads
            inflation_shock: Change in inflation expectations
            
        Returns:
            Dict[str, float]: Stress test results including key metrics
        """
        stressed_assets = self.calculate_stressed_assets(
            interest_rate_shock, credit_spread_shock, inflation_shock
        )
        stressed_liabilities = self.calculate_stressed_liabilities(
            interest_rate_shock, inflation_shock
        )
        
        return {
            "stressed_funding_ratio": stressed_assets / stressed_liabilities,
            "stressed_duration_gap": self.calculate_stressed_duration_gap(interest_rate_shock),
            "stressed_liquidity_ratio": self.calculate_stressed_liquidity_ratio()
        }

    def optimize_portfolio(self) -> Dict[str, float]:
        """
        Optimize the portfolio allocation considering multiple objectives.
        
        This method implements a multi-objective optimization considering:
        - Funding ratio target
        - Duration matching
        - Cash flow matching
        - Risk constraints
        
        Returns:
            Dict[str, float]: Optimal asset allocation weights
        """
        # Implementation would use optimization library like scipy.optimize
        pass

# Example usage:
if __name__ == "__main__":
    # Create ALM strategy instance
    alm_strategy = ALMStrategy(
        initial_assets=1000000,
        target_funding_ratio=1.05,
        max_duration_gap=1.0,
        min_liquidity_ratio=0.15
    )
    
    # Add sample liability cash flows
    alm_strategy.liability_cashflows.append(
        LiabilityCashFlow(
            time_period=1,
            expected_amount=50000,
            uncertainty=0.05,
            discounted_value=48000
        )
    )
    
    # Run ALM assessment
    rebalancing_needs = alm_strategy.assess_rebalancing_needs()
    stress_test_results = alm_strategy.run_stress_test(
        interest_rate_shock=0.01,
        credit_spread_shock=0.005,
        inflation_shock=0.02
    ) 