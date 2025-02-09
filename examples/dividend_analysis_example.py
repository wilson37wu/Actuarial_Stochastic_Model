"""
Example script demonstrating dividend analysis and visualization features.
"""
import numpy as np
from datetime import date
import matplotlib.pyplot as plt
from src.dividend_tracker import DividendTracker
from src.gcv_calculator import GCVCalculator, GradingPattern, ProductVariant
from src.visualization import ModelVisualizer

def main():
    # Initialize components
    tracker = DividendTracker(
        minimum_dividend_rate=0.01,
        shareholder_cost_rate=0.02
    )
    calculator = GCVCalculator()
    visualizer = ModelVisualizer()
    
    # Set up example policies
    policies = ['POL001', 'POL002', 'POL003']
    face_amounts = [100000, 150000, 200000]
    
    # Initialize accounts
    for policy in policies:
        tracker.initialize_account(policy)
    
    # Generate some example asset returns
    np.random.seed(42)  # For reproducibility
    returns = np.random.normal(0.06, 0.12, size=20)  # 20 periods, mean 6%, vol 12%
    
    # Process returns for each policy
    for policy, face_amount in zip(policies, face_amounts):
        for ret in returns:
            tracker.calculate_dividend(
                policy_number=policy,
                asset_return=ret,
                face_amount=face_amount,
                valuation_date=date.today()
            )
    
    # 1. Visualize GCV Patterns
    visualizer.plot_gcv_patterns(
        max_years=30,
        premium=5000,
        face_amount=100000,
        cash_value=80000
    )
    
    # 2. Visualize Product Variants
    visualizer.plot_product_variant_gcv(
        calculator=calculator,
        premium=5000,
        face_amount=100000,
        pv_premium=80000,
        max_years=30,
        save_path='outputs/product_variants.png'
    )
    
    # 3. Analyze Dividends
    visualizer.plot_dividend_analysis(
        tracker=tracker,
        policy_numbers=policies,
        save_path='outputs/dividend_analysis.png'
    )
    
    # 4. Run Stress Tests
    scenarios = {
        'Base': returns,
        'High_Vol': np.random.normal(0.06, 0.18, size=20),
        'Low_Return': np.random.normal(0.03, 0.12, size=20),
        'Crisis': np.concatenate([
            np.random.normal(-0.15, 0.25, size=5),
            np.random.normal(0.08, 0.12, size=15)
        ])
    }
    
    stress_results = tracker.run_stress_test(
        policy_number=policies[0],
        face_amount=face_amounts[0],
        scenarios=scenarios
    )
    
    visualizer.plot_stress_test_results(
        results=stress_results,
        save_path='outputs/stress_test.png'
    )
    
    # 5. Generate Recovery Analysis
    for policy in policies:
        # Get recovery metrics
        metrics = tracker.analyze_recovery_metrics(policy)
        print(f"\nRecovery Metrics for {policy}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
        
        # Generate detailed report
        report = tracker.generate_dividend_report(policy)
        report.to_excel(f'outputs/{policy}_dividend_report.xlsx')
        
        # Project recovery path
        if tracker.accounts[policy].tracking_balance < 0:
            recovery = tracker.project_recovery_path(
                policy_number=policy,
                assumed_return=0.06,
                projection_years=10
            )
            print(f"\nRecovery Projection for {policy}:")
            print(recovery)

if __name__ == '__main__':
    main()
