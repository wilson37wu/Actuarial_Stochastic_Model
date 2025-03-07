"""
ALM Calculations Module

This module provides utility functions for ALM calculations,
including present value, duration, convexity, and risk metrics.
"""

import numpy as np
from typing import List, Tuple

def calculate_present_value(
    cash_flows: List[float],
    times: List[float],
    discount_rates: List[float]
) -> float:
    """
    Calculate present value of cash flows using specified discount rates.
    
    Args:
        cash_flows: List of cash flow amounts
        times: List of times when cash flows occur
        discount_rates: List of discount rates for each cash flow
        
    Returns:
        float: Present value of the cash flows
    """
    return sum(
        cf / (1 + r) ** t
        for cf, t, r in zip(cash_flows, times, discount_rates)
    )

def calculate_duration(
    cash_flows: List[float],
    times: List[float],
    discount_rate: float
) -> float:
    """
    Calculate Macaulay duration of a series of cash flows.
    
    Args:
        cash_flows: List of cash flow amounts
        times: List of times when cash flows occur
        discount_rate: Single discount rate for all cash flows
        
    Returns:
        float: Macaulay duration
    """
    pv = calculate_present_value(cash_flows, times, [discount_rate] * len(times))
    weighted_times = sum(
        t * cf / (1 + discount_rate) ** t
        for t, cf in zip(times, cash_flows)
    )
    return weighted_times / pv if pv > 0 else 0

def calculate_convexity(
    cash_flows: List[float],
    times: List[float],
    discount_rate: float
) -> float:
    """
    Calculate convexity of a series of cash flows.
    
    Args:
        cash_flows: List of cash flow amounts
        times: List of times when cash flows occur
        discount_rate: Single discount rate for all cash flows
        
    Returns:
        float: Convexity measure
    """
    pv = calculate_present_value(cash_flows, times, [discount_rate] * len(times))
    weighted_times_squared = sum(
        t * (t + 1) * cf / (1 + discount_rate) ** t
        for t, cf in zip(times, cash_flows)
    )
    return weighted_times_squared / (pv * (1 + discount_rate) ** 2) if pv > 0 else 0

def calculate_funding_ratio_volatility(
    asset_volatility: float,
    liability_volatility: float,
    correlation: float,
    current_funding_ratio: float
) -> float:
    """
    Calculate the volatility of the funding ratio.
    
    Args:
        asset_volatility: Volatility of assets
        liability_volatility: Volatility of liabilities
        correlation: Correlation between assets and liabilities
        current_funding_ratio: Current ratio of assets to liabilities
        
    Returns:
        float: Annualized funding ratio volatility
    """
    return current_funding_ratio * np.sqrt(
        asset_volatility**2 + liability_volatility**2 -
        2 * correlation * asset_volatility * liability_volatility
    )

def calculate_var_cvar(
    returns: List[float],
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Value at Risk and Conditional Value at Risk.
    
    Args:
        returns: List of historical returns
        confidence_level: Statistical confidence level (default: 0.95)
        
    Returns:
        Tuple[float, float]: (VaR, CVaR) at specified confidence level
    """
    returns_array = np.array(returns)
    var = np.percentile(returns_array, (1 - confidence_level) * 100)
    cvar = np.mean(returns_array[returns_array <= var])
    return var, cvar

def calculate_liquidity_score(
    asset_cashflows: List[float],
    liability_cashflows: List[float],
    time_periods: List[int]
) -> float:
    """
    Calculate liquidity score based on cash flow matching.
    
    Args:
        asset_cashflows: List of asset cash flows
        liability_cashflows: List of liability cash flows
        time_periods: List of time periods
        
    Returns:
        float: Weighted average liquidity score
    """
    coverage_ratios = []
    for t, (asset_cf, liability_cf) in enumerate(zip(asset_cashflows, liability_cashflows)):
        if liability_cf > 0:
            coverage_ratios.append(asset_cf / liability_cf)
        else:
            coverage_ratios.append(float('inf'))
    
    # Weight recent periods more heavily
    weights = np.exp(-0.1 * np.array(time_periods))
    weights = weights / np.sum(weights)
    
    return np.average(coverage_ratios, weights=weights)

def stress_test_portfolio(
    portfolio_value: float,
    duration: float,
    convexity: float,
    interest_rate_shock: float,
    credit_spread_shock: float = 0,
    equity_shock: float = 0
) -> float:
    """
    Perform stress test on portfolio value under multiple risk factors.
    
    Args:
        portfolio_value: Current market value of portfolio
        duration: Portfolio duration
        convexity: Portfolio convexity
        interest_rate_shock: Parallel shift in interest rates
        credit_spread_shock: Widening of credit spreads (default: 0)
        equity_shock: Equity market shock (default: 0)
        
    Returns:
        float: Stressed portfolio value
    """
    # First order and second order interest rate effects
    ir_effect = -duration * interest_rate_shock + 0.5 * convexity * interest_rate_shock**2
    
    # Credit spread effect (simplified)
    credit_effect = -duration * credit_spread_shock
    
    # Equity effect (if applicable)
    equity_effect = equity_shock
    
    # Total effect
    total_effect = ir_effect + credit_effect + equity_effect
    
    return portfolio_value * (1 + total_effect)

def calculate_tracking_error(
    portfolio_returns: List[float],
    benchmark_returns: List[float]
) -> float:
    """
    Calculate tracking error versus benchmark.
    
    Args:
        portfolio_returns: List of portfolio returns
        benchmark_returns: List of benchmark returns
        
    Returns:
        float: Annualized tracking error
    """
    return np.std(np.array(portfolio_returns) - np.array(benchmark_returns))

def optimize_rebalancing_threshold(
    funding_ratio_volatility: float,
    transaction_costs: float,
    risk_aversion: float
) -> float:
    """
    Calculate optimal rebalancing threshold based on cost-risk tradeoff.
    
    Args:
        funding_ratio_volatility: Volatility of funding ratio
        transaction_costs: Cost of rebalancing
        risk_aversion: Risk aversion parameter
        
    Returns:
        float: Optimal rebalancing threshold
    """
    return np.sqrt(2 * transaction_costs / (risk_aversion * funding_ratio_volatility)) 