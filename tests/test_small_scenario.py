"""
Test scenario generation with minimal policies for debugging.
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import date
import logging
from typing import List, Dict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.economic_scenario import EconomicScenarioGenerator, EconomicFactors
from src.cash_flow_model import DynamicCashFlowModel, CashFlow
from src.financial_models import ModelParameters, ALMEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_test_policies() -> pd.DataFrame:
    """Generate two sample policies for testing."""
    return pd.DataFrame({
        'policy_id': [1, 2],
        'age': [35, 45],
        'gender': ['M', 'F'],
        'face_amount': [100000.0, 150000.0],
        'premium': [1200.0, 1800.0],
        'account_value': [50000.0, 75000.0],
    })

def generate_simple_mortality_table() -> pd.DataFrame:
    """Generate a simple mortality table."""
    ages = range(0, 100)
    return pd.DataFrame({
        'age': ages,
        'mortality_rate': [min(0.001 * (1.08 ** age), 1.0) for age in ages]
    }).set_index('age')

def test_minimal_scenario_generation():
    """Test scenario generation with minimal setup."""
    try:
        # Initialize economic scenario generator
        logging.info("Initializing economic scenario generator...")
        esg = EconomicScenarioGenerator(
            initial_short_rate=0.02,
            initial_long_rate=0.03,
            mean_reversion_speed=0.15,
            volatility_short_rate=0.01,
            volatility_long_rate=0.008,
            equity_risk_premium=0.05,
            equity_volatility=0.15,
            inflation_mean=0.02,
            inflation_volatility=0.01
        )
        
        # Generate a small number of scenarios
        num_scenarios = 2
        projection_years = 5
        time_steps = 12
        
        logging.info(f"Generating {num_scenarios} scenarios for {projection_years} years...")
        scenarios = esg.generate_scenarios(
            num_scenarios=num_scenarios,
            projection_years=projection_years,
            time_steps_per_year=time_steps
        )
        
        # Log scenario details
        logging.info("\nScenario Details:")
        for scenario_idx, scenario in enumerate(scenarios):
            logging.info(f"\nScenario {scenario_idx + 1}:")
            for time_idx, factors in enumerate(scenario[:3]):  # Show first 3 time steps
                logging.info(f"Time Step {time_idx}:")
                logging.info(f"- Short Rate: {factors.short_rate:.4f}")
                logging.info(f"- Long Rate: {factors.long_rate:.4f}")
                logging.info(f"- Equity Return: {factors.equity_return:.4f}")
                logging.info(f"- Inflation: {factors.inflation_rate:.4f}")
                logging.info(f"- Credit Spread: {factors.credit_spread:.4f}")
        
        # Initialize cash flow model
        logging.info("\nInitializing cash flow model...")
        policy_data = generate_test_policies()
        mortality_table = generate_simple_mortality_table()
        
        cfm = DynamicCashFlowModel(
            initial_assets=1000000.0,  # 1M initial assets
            mortality_table=mortality_table,
            lapse_rates={i: 0.05 for i in range(projection_years)},  # 5% flat lapse rate
            expense_factors={'acquisition': 0.02, 'maintenance': 0.01},
            investment_strategy={'bonds': 0.8, 'equities': 0.2}
        )
        
        # Project cash flows
        logging.info("\nProjecting cash flows...")
        liability_flows = cfm.project_liability_flows(scenarios, policy_data)
        asset_flows = cfm.project_asset_flows(scenarios, liability_flows)
        
        # Log cash flow details
        logging.info("\nCash Flow Details:")
        flow_types = {'premium', 'death_benefit', 'surrender_benefit'}
        for flow_type in flow_types:
            type_flows = [flow for flow in liability_flows if flow.flow_type == flow_type]
            if type_flows:
                total_amount = sum(flow.amount for flow in type_flows)
                avg_amount = total_amount / len(type_flows)
                logging.info(f"{flow_type.title()}:")
                logging.info(f"- Count: {len(type_flows)}")
                logging.info(f"- Total: ${total_amount:,.2f}")
                logging.info(f"- Average: ${avg_amount:,.2f}")
        
        # Calculate and log risk metrics
        logging.info("\nCalculating risk metrics...")
        metrics = cfm.calculate_risk_metrics(liability_flows, asset_flows)
        logging.info(f"Risk Metrics:")
        logging.info(f"- VaR(95): ${metrics['var_95']:,.2f}")
        logging.info(f"- CTE(95): ${metrics['cte_95']:,.2f}")
        
        logging.info("\nTest completed successfully!")
        
        # Add assertions to verify the test results
        assert len(scenarios) == num_scenarios, f"Expected {num_scenarios} scenarios, got {len(scenarios)}"
        assert all(len(scenario) == projection_years * time_steps for scenario in scenarios), "Incorrect number of time steps"
        
        # Verify economic factors are within reasonable bounds
        for scenario in scenarios:
            for factors in scenario:
                assert -0.1 <= factors.short_rate <= 0.2, f"Short rate {factors.short_rate} outside reasonable bounds"
                assert -0.1 <= factors.long_rate <= 0.3, f"Long rate {factors.long_rate} outside reasonable bounds"
                assert -0.5 <= factors.equity_return <= 0.5, f"Equity return {factors.equity_return} outside reasonable bounds"
                assert -0.1 <= factors.inflation_rate <= 0.1, f"Inflation rate {factors.inflation_rate} outside reasonable bounds"
                assert 0 <= factors.credit_spread <= 0.2, f"Credit spread {factors.credit_spread} outside reasonable bounds"
        
        # Verify cash flows
        assert len(liability_flows) > 0, "No liability cash flows generated"
        assert len(asset_flows) > 0, "No asset cash flows generated"
        
        # Verify risk metrics
        assert metrics['var_95'] < 0, "VaR(95) should be negative for liability flows"
        assert metrics['cte_95'] <= metrics['var_95'], "CTE(95) should be less than or equal to VaR(95)"
        assert metrics['std_npv'] > 0, "Standard deviation should be positive"
        
    except Exception as e:
        logging.error(f"Error in minimal scenario test: {e}")
        raise

if __name__ == "__main__":
    test_minimal_scenario_generation()
