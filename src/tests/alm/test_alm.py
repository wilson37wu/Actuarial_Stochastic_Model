"""
Test script for Asset Liability Management (ALM) module.
This script demonstrates the key functionalities of the ALM framework.
"""

import numpy as np
from typing import List, Dict
from alm_strategy import ALMStrategy, LiabilityCashFlow, AssetCashFlow
from alm_utils import (
    calculate_present_value,
    calculate_duration,
    calculate_convexity,
    stress_test_portfolio
)
from alm_config import ALMConfig, DEFAULT_ASSET_CLASSES
from alm_reporting import generate_alm_report
import pandas as pd

def test_basic_alm_setup():
    """Test basic ALM strategy setup and configuration"""
    print("\n=== Testing Basic ALM Setup ===")
    
    # Initialize ALM strategy
    strategy = ALMStrategy(
        initial_assets=1000000,
        target_funding_ratio=1.05,
        max_duration_gap=1.0,
        min_liquidity_ratio=0.15
    )
    
    print(f"Initial assets: ${strategy.initial_assets:,.2f}")
    print(f"Target funding ratio: {strategy.target_funding_ratio:.2%}")
    print(f"Maximum duration gap: {strategy.max_duration_gap:.1f}")
    print(f"Minimum liquidity ratio: {strategy.min_liquidity_ratio:.2%}")
    
    return strategy

def test_liability_cashflows(strategy: ALMStrategy):
    """Test liability cash flow management"""
    print("\n=== Testing Liability Cash Flows ===")
    
    # Add sample liability cash flows
    liability_cashflows = [
        LiabilityCashFlow(
            time_period=t,
            expected_amount=50000 * (1.02 ** t),  # Growing at 2% per year
            uncertainty=0.05 + 0.01 * t,  # Increasing uncertainty with time
            discounted_value=50000 * (1.02 ** t) / (1.05 ** t)  # Discounted at 5%
        )
        for t in range(1, 6)
    ]
    
    strategy.liability_cashflows.extend(liability_cashflows)
    
    print("\nLiability Cash Flows:")
    print("Year | Expected Amount | Uncertainty | PV")
    print("-" * 50)
    for lcf in strategy.liability_cashflows:
        print(f"{lcf.time_period:4d} | ${lcf.expected_amount:13,.2f} | "
              f"{lcf.uncertainty:10.2%} | ${lcf.discounted_value:10,.2f}")
    
    return [lcf.expected_amount for lcf in liability_cashflows]

def test_asset_allocation(strategy: ALMStrategy):
    """Test asset allocation and portfolio characteristics"""
    print("\n=== Testing Asset Allocation ===")
    
    # Create sample asset cash flows
    asset_cashflows = [
        AssetCashFlow(
            time_period=1,
            expected_amount=30000,
            duration=0.95,
            credit_quality="AAA"
        ),
        AssetCashFlow(
            time_period=2,
            expected_amount=35000,
            duration=1.90,
            credit_quality="AA"
        ),
        AssetCashFlow(
            time_period=3,
            expected_amount=40000,
            duration=2.85,
            credit_quality="A"
        ),
        AssetCashFlow(
            time_period=4,
            expected_amount=45000,
            duration=3.80,
            credit_quality="AA"
        ),
        AssetCashFlow(
            time_period=5,
            expected_amount=50000,
            duration=4.75,
            credit_quality="AAA"
        )
    ]
    
    strategy.asset_cashflows.extend(asset_cashflows)
    
    print("\nAsset Cash Flows:")
    print("Year | Expected Amount | Duration | Credit Quality")
    print("-" * 55)
    for acf in asset_cashflows:
        print(f"{acf.time_period:4d} | ${acf.expected_amount:13,.2f} | "
              f"{acf.duration:8.2f} | {acf.credit_quality:>13}")
    
    return [acf.expected_amount for acf in asset_cashflows]

def test_risk_metrics(cash_flows: List[float]) -> tuple[Dict[str, List[float]], Dict[str, float]]:
    """Test risk metrics calculations"""
    print("\n=== Testing Risk Metrics ===")
    
    times = list(range(1, len(cash_flows) + 1))
    discount_rate = 0.05
    
    # Calculate key metrics for each year
    durations = []
    convexities = []
    stress_impacts = []
    
    for t in range(len(cash_flows)):
        current_flows = cash_flows[:t+1]
        current_times = times[:t+1]
        
        if current_flows:
            duration = calculate_duration(current_flows, current_times, discount_rate)
            convexity = calculate_convexity(current_flows, current_times, discount_rate)
            
            # Stress test
            portfolio_value = sum(current_flows)
            stressed_value = stress_test_portfolio(
                portfolio_value=portfolio_value,
                duration=duration,
                convexity=convexity,
                interest_rate_shock=0.01,
                credit_spread_shock=0.005,
                equity_shock=-0.05
            )
            stress_impact = (stressed_value/portfolio_value - 1) * 100
        else:
            duration = 0
            convexity = 0
            stress_impact = 0
        
        durations.append(duration)
        convexities.append(convexity)
        stress_impacts.append(stress_impact)
    
    # Calculate final metrics for display
    final_pv = calculate_present_value(cash_flows, times, [discount_rate] * len(times))
    final_duration = durations[-1]
    final_convexity = convexities[-1]
    
    print(f"Present Value: ${final_pv:,.2f}")
    print(f"Duration: {final_duration:.2f} years")
    print(f"Convexity: {final_convexity:.2f}")
    
    # Final stress test for display
    portfolio_value = 1000000
    stressed_value = stress_test_portfolio(
        portfolio_value=portfolio_value,
        duration=final_duration,
        convexity=final_convexity,
        interest_rate_shock=0.01,
        credit_spread_shock=0.005,
        equity_shock=-0.05
    )
    
    print("\nStress Test Results:")
    print(f"Original Portfolio Value: ${portfolio_value:,.2f}")
    print(f"Stressed Portfolio Value: ${stressed_value:,.2f}")
    print(f"Change: {(stressed_value/portfolio_value - 1):.2%}")
    
    risk_metrics = {
        'Duration': durations,
        'Convexity': convexities,
        'Stress Impact': stress_impacts
    }
    
    stress_results = {
        'Stressed Value': stressed_value,
        'Value Change': stressed_value - portfolio_value,
        'Percentage Change': (stressed_value/portfolio_value - 1)
    }
    
    return risk_metrics, stress_results

def test_asset_classes():
    """Test asset class configurations"""
    print("\n=== Testing Asset Classes ===")
    
    print("\nDefault Asset Class Characteristics:")
    print("Asset Class | Expected Return | Volatility | Duration | Credit Quality | Liquidity")
    print("-" * 80)
    
    for asset_class, config in DEFAULT_ASSET_CLASSES.items():
        print(f"{asset_class:11s} | {config.expected_return:13.2%} | "
              f"{config.volatility:9.2%} | {config.duration:8.1f} | "
              f"{config.credit_quality:>13} | {config.liquidity_score:9.1f}")

def main():
    """Run all ALM tests and generate reports"""
    print("Starting ALM Module Tests...")
    
    # Run tests and collect data for reporting
    strategy = test_basic_alm_setup()
    liability_cfs = test_liability_cashflows(strategy)
    asset_cfs = test_asset_allocation(strategy)
    risk_metrics, stress_results = test_risk_metrics(asset_cfs)
    test_asset_classes()
    
    # Generate comprehensive report
    print("\nGenerating ALM reports...")
    generate_alm_report(
        strategy=strategy,
        liability_cfs=liability_cfs,
        asset_cfs=asset_cfs,
        risk_metrics=risk_metrics,
        stress_results=stress_results
    )
    
    print("\nALM Module Tests Completed.")
    print("Reports have been generated - check alm_report_*.xlsx and alm_dashboard.png")

if __name__ == "__main__":
    main() 