"""
Performance testing for cash flow model with vectorized operations.

This module tests the performance of the DynamicCashFlowModel, particularly focusing on:
1. Vectorized operations for large policy datasets
2. Parallel scenario generation and processing
3. Memory usage optimization
4. Processing time benchmarks

The tests use realistic sample sizes and compare performance metrics.
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import date, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
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

def generate_sample_policy_data(num_policies: int = 1000) -> pd.DataFrame:
    """
    Generate sample policy data for testing using vectorized operations.
    
    Args:
        num_policies (int): Number of policies to generate
        
    Returns:
        pd.DataFrame: DataFrame containing policy data
    """
    return pd.DataFrame({
        'policy_id': range(num_policies),
        'face_amount': np.random.uniform(50000, 500000, num_policies),
        'premium': np.random.uniform(1000, 5000, num_policies),
        'account_value': np.random.uniform(10000, 100000, num_policies),
        'date_of_birth': pd.date_range(start='1960-01-01', periods=num_policies, freq='D'),
        'sex': np.random.choice(['M', 'F'], num_policies),
        'smoker_status': np.random.choice(['Y', 'N'], num_policies)
    })

def generate_sample_mortality_table() -> pd.DataFrame:
    """
    Generate sample mortality table using vectorized operations.
    
    Returns:
        pd.DataFrame: DataFrame containing mortality rates
    """
    ages = range(20, 100)
    return pd.DataFrame({
        'age': ages,
        'sex': 'M',
        'smoker_status': 'N',
        'mortality_rate': [0.001 * (1.05 ** (age - 20)) for age in ages]
    })

def test_economic_scenario_generation():
    """Test economic scenario generation."""
    start_time = time.time()
    logging.info(f"Starting economic scenario generation test with 1000 scenarios")
    
    try:
        # Initialize generator with default parameters
        esg = EconomicScenarioGenerator()
        
        # Generate scenarios
        scenarios = esg.generate_scenarios(
            num_scenarios=1000,
            projection_years=30,
            time_steps_per_year=12
        )
        
        # Validate scenarios
        total_steps = 30 * 12
        assert len(scenarios) == 1000, "Wrong number of scenarios"
        assert len(scenarios[0]) == total_steps, "Wrong number of time steps"
        
        # Check for invalid values
        for scenario in scenarios:
            for factors in scenario:
                assert 0 <= factors.short_rate <= 0.15, f"Invalid short rate: {factors.short_rate}"
                assert 0 <= factors.long_rate <= 0.20, f"Invalid long rate: {factors.long_rate}"
                assert -0.5 <= factors.equity_return <= 0.5, f"Invalid equity return: {factors.equity_return}"
                assert -0.05 <= factors.inflation_rate <= 0.15, f"Invalid inflation: {factors.inflation_rate}"
                assert 0 <= factors.credit_spread <= 0.10, f"Invalid credit spread: {factors.credit_spread}"
        
        duration = time.time() - start_time
        logging.info(f"Economic scenario generation completed successfully in {duration:.2f} seconds")
        
    except Exception as e:
        logging.error(f"Error in economic scenario generation: {e}")
        raise

def test_cash_flow_model_performance():
    """Test cash flow model performance with vectorized operations."""
    start_time = time.time()
    
    # Generate test data
    policy_data = generate_sample_policy_data(10000)  # Test with 10k policies
    mortality_table = generate_sample_mortality_table()
    
    # Initialize model with vectorized capabilities
    model = DynamicCashFlowModel(
        initial_assets=1000000,
        mortality_table=mortality_table,
        lapse_rates=pd.Series({i: 0.05 * (0.95 ** i) for i in range(20)}),
        expense_factors=pd.Series({'acquisition': 0.02, 'maintenance': 0.01}),
        investment_strategy={'fixed_income': 0.7, 'equity': 0.3}
    )
    
    # Generate scenarios
    scenario_gen = EconomicScenarioGenerator()
    scenarios = scenario_gen.generate_scenarios(
        start_date=date.today(),
        num_scenarios=100,
        projection_years=30
    )
    
    # Measure projection time
    proj_start = time.time()
    liability_flows = model.project_liability_flows(scenarios, policy_data)
    asset_flows = model.project_asset_flows(scenarios, liability_flows)
    proj_end = time.time()
    
    # Log performance metrics
    logging.info(f"Total policies processed: {len(policy_data)}")
    logging.info(f"Total scenarios: {len(scenarios)}")
    logging.info(f"Projection time: {proj_end - proj_start:.2f} seconds")
    logging.info(f"Processing rate: {len(policy_data) * len(scenarios) / (proj_end - proj_start):.0f} policy-scenarios/second")

def parallel_scenario_test(worker_id: int, scenario_batch: int) -> List[List[EconomicFactors]]:
    """Generate a batch of scenarios for parallel processing."""
    try:
        esg = EconomicScenarioGenerator()
        logging.info(f"Worker {worker_id}: Starting generation of {scenario_batch} scenarios")
        
        scenarios = esg.generate_scenarios(
            num_scenarios=scenario_batch,
            projection_years=5,  # Reduced for testing
            time_steps_per_year=12
        )
        
        logging.info(f"Worker {worker_id}: Successfully generated {len(scenarios)} scenarios")
        return scenarios
    except Exception as e:
        logging.error(f"Worker {worker_id}: Error in parallel batch generation: {e}")
        raise

def test_parallel_scenario_generation():
    """Test parallel scenario generation."""
    start_time = time.time()
    total_scenarios = 1000  # Reduced for testing
    num_workers = min(4, os.cpu_count() or 4)  # Limit workers
    
    logging.info(f"Starting parallel scenario generation:")
    logging.info(f"- Total scenarios target: {total_scenarios}")
    logging.info(f"- Number of workers: {num_workers}")
    logging.info(f"- Scenarios per worker: {total_scenarios // num_workers}")
    
    scenarios_per_worker = total_scenarios // num_workers
    completed_scenarios = 0
    
    try:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            # Submit tasks with worker IDs
            for worker_id in range(num_workers):
                future = executor.submit(parallel_scenario_test, worker_id, scenarios_per_worker)
                futures.append(future)
            
            all_scenarios = []
            for i, future in enumerate(as_completed(futures)):
                try:
                    scenarios = future.result(timeout=300)  # 5 minute timeout
                    if scenarios:
                        batch_size = len(scenarios)
                        all_scenarios.extend(scenarios)
                        completed_scenarios += batch_size
                        
                        # Calculate progress
                        progress = (completed_scenarios / total_scenarios) * 100
                        elapsed_time = time.time() - start_time
                        rate = completed_scenarios / elapsed_time if elapsed_time > 0 else 0
                        
                        # Log detailed progress
                        logging.info(f"Progress Update:")
                        logging.info(f"- Completed batch {i+1}/{num_workers}")
                        logging.info(f"- Scenarios in this batch: {batch_size}")
                        logging.info(f"- Total scenarios so far: {completed_scenarios}/{total_scenarios}")
                        logging.info(f"- Progress: {progress:.1f}%")
                        logging.info(f"- Generation rate: {rate:.1f} scenarios/second")
                        logging.info(f"- Elapsed time: {elapsed_time:.1f} seconds")
                        
                except Exception as e:
                    logging.error(f"Error in parallel processing batch {i+1}: {e}")
                    raise
        
        # Validate results
        assert len(all_scenarios) > 0, "No scenarios generated"
        expected_steps = 5 * 12  # projection_years * time_steps_per_year
        assert len(all_scenarios[0]) == expected_steps, f"Wrong number of time steps: {len(all_scenarios[0])} vs expected {expected_steps}"
        
        # Final statistics
        final_duration = time.time() - start_time
        final_rate = len(all_scenarios) / final_duration if final_duration > 0 else 0
        
        logging.info("\nFinal Results:")
        logging.info(f"- Total scenarios generated: {len(all_scenarios)}")
        logging.info(f"- Total time: {final_duration:.1f} seconds")
        logging.info(f"- Average generation rate: {final_rate:.1f} scenarios/second")
        logging.info(f"- Scenarios per worker: {len(all_scenarios)/num_workers:.1f}")
        
        # Validate total count
        assert abs(len(all_scenarios) - total_scenarios) <= num_workers, \
            f"Generated scenario count ({len(all_scenarios)}) significantly differs from target ({total_scenarios})"
        
        return all_scenarios
        
    except Exception as e:
        logging.error(f"Parallel scenario generation failed: {e}")
        logging.error(f"- Completed scenarios before failure: {completed_scenarios}")
        logging.error(f"- Progress before failure: {(completed_scenarios/total_scenarios)*100:.1f}%")
        raise

if __name__ == "__main__":
    try:
        # Test economic scenario generation
        logging.info("=== Testing Economic Scenario Generation ===")
        test_economic_scenario_generation()
        
        # Test parallel scenario generation
        logging.info("\n=== Testing Parallel Scenario Generation ===")
        test_parallel_scenario_generation()
        
        # Test cash flow model performance
        logging.info("\n=== Testing Cash Flow Model Performance ===")
        test_cash_flow_model_performance()
        
        logging.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logging.error(f"Test suite failed: {e}")
        raise
