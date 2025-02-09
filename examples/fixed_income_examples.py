import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import date, timedelta
import matplotlib.pyplot as plt
from src.fixed_income import Bond, FixedIncomeModel
from src.asset_model import AssetModel
import matplotlib.dates as mdates

def create_sample_portfolio():
    """Create a sample bond portfolio with diverse characteristics."""
    today = date.today()
    
    bonds = [
        Bond(
            id="GOVT_5Y",
            par_value=1000000.0,
            coupon_rate=0.035,  # 3.5% government bond
            maturity_date=today + timedelta(days=365*5),
            payment_frequency=2,
            credit_rating="AAA",
            issue_date=today,
            purchase_price=980000.0  # Slight discount
        ),
        Bond(
            id="CORP_3Y_A",
            par_value=500000.0,
            coupon_rate=0.045,  # 4.5% corporate bond
            maturity_date=today + timedelta(days=365*3),
            payment_frequency=2,
            credit_rating="A",
            issue_date=today,
            purchase_price=505000.0  # Slight premium
        ),
        Bond(
            id="CORP_7Y_BBB",
            par_value=750000.0,
            coupon_rate=0.055,  # 5.5% corporate bond
            maturity_date=today + timedelta(days=365*7),
            payment_frequency=4,  # Quarterly payments
            credit_rating="BBB",
            issue_date=today,
            purchase_price=750000.0  # Par
        )
    ]
    return bonds

def generate_scenarios(num_scenarios: int, projection_years: int):
    """Generate economic scenarios for testing."""
    today = date.today()
    dates = pd.date_range(start=today, periods=projection_years*12, freq='M')
    
    scenarios = []
    for i in range(num_scenarios):
        # Base risk-free rate path with mean reversion
        base_rate = 0.03  # 3% base rate
        volatility = 0.002
        mean_reversion = 0.1
        
        rates = [base_rate]
        for t in range(len(dates)-1):
            dr = mean_reversion * (base_rate - rates[-1]) + \
                 volatility * np.random.normal()
            rates.append(rates[-1] + dr)
        
        # Credit spreads correlated with rates
        spreads = [max(0.001, r * 0.2 + 0.005 + 0.001 * np.random.normal()) 
                  for r in rates]
        
        scenario = pd.DataFrame({
            'risk_free_rate': rates,
            'credit_spread': spreads
        }, index=dates)
        scenarios.append(scenario)
    
    return scenarios

def example_1_basic_projection():
    """Example 1: Basic cash flow projection for a single bond."""
    print("\nExample 1: Basic Cash Flow Projection")
    print("-" * 50)
    
    # Create a single bond
    today = date.today()
    bond = Bond(
        id="EXAMPLE_1",
        par_value=1000000.0,
        coupon_rate=0.04,
        maturity_date=today + timedelta(days=365*5),
        payment_frequency=2,
        credit_rating="AA",
        issue_date=today,
        purchase_price=1000000.0
    )
    
    # Create model and project cash flows
    model = FixedIncomeModel({})
    scenario = generate_scenarios(1, 5)[0]  # Single scenario, 5 years
    
    # Convert dates to datetime for proper indexing
    projection_dates = [pd.Timestamp(d).date() for d in scenario.index]
    
    cashflows = model.project_cashflows(bond, projection_dates, scenario)
    
    print(f"\nProjected cash flows for {bond.id}:")
    print("\nFirst few cash flows:")
    print(cashflows.head().to_string())
    print(f"\nTotal projected coupon payments: ${cashflows['coupon_payment'].sum():,.2f}")
    print(f"Total projected principal payments: ${cashflows['principal_payment'].sum():,.2f}")

def example_2_portfolio_metrics():
    """Example 2: Calculate and display portfolio metrics."""
    print("\nExample 2: Portfolio Metrics")
    print("-" * 50)
    
    bonds = create_sample_portfolio()
    asset_model = AssetModel({})
    
    # Create a simple yield curve
    terms = [0.25, 0.5, 1, 2, 3, 5, 7, 10]
    rates = [0.025, 0.028, 0.03, 0.032, 0.034, 0.036, 0.037, 0.038]
    yield_curve = pd.Series(rates, index=terms)
    
    metrics = asset_model.calculate_portfolio_metrics(bonds, yield_curve)
    
    print("\nPortfolio Metrics:")
    for bond in bonds:
        print(f"\nBond: {bond.id}")
        print(f"Par Value: ${bond.par_value:,.2f}")
        print(f"Coupon Rate: {bond.coupon_rate:.1%}")
        print(f"Credit Rating: {bond.credit_rating}")
    
    print("\nAggregated Portfolio Metrics:")
    print(f"Total Market Value: ${metrics['total_market_value']:,.2f}")
    print(f"Weighted Duration: {metrics['weighted_duration']:.2f} years")
    print(f"Weighted Convexity: {metrics['weighted_convexity']:.2f}")

def example_3_scenario_analysis():
    """Example 3: Multi-scenario analysis with visualization."""
    print("\nExample 3: Scenario Analysis")
    print("-" * 50)
    
    bonds = create_sample_portfolio()
    asset_model = AssetModel({})
    
    # Get timeline from first bond
    first_bond = bonds[0]
    payment_dates = first_bond.payment_dates
    
    # Run projections (simplified for example)
    num_scenarios = 100
    cash_flows = np.zeros((num_scenarios, len(payment_dates)))
    
    # Simulate random cash flows (replace with actual model logic)
    for i in range(num_scenarios):
        base_cf = np.exp(-0.1 * np.arange(len(payment_dates)))  # Decay pattern
        noise = np.random.normal(0, 0.1, len(payment_dates))
        cash_flows[i] = base_cf + noise
    cash_flows = np.maximum(cash_flows, 0)  # Ensure non-negative
    
    # Find last non-zero cash flow across all scenarios
    aggregate_cf = cash_flows.sum(axis=0)
    last_active_idx = np.max(np.where(aggregate_cf > 0)[0])
    trim_date = payment_dates[last_active_idx]
    
    # Plotting
    plt.figure(figsize=(12, 6))
    for i in range(num_scenarios):
        plt.plot(
            payment_dates[:last_active_idx+1],
            cash_flows[i, :last_active_idx+1],
            alpha=0.1,
            color='blue',
            linewidth=0.8
        )
    
    # Format dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))
    plt.gcf().autofmt_xdate()
    
    plt.title(f"Scenario Cash Flows ({first_bond.projection_start:%Y-%m} to {trim_date:%Y-%m})")
    plt.xlabel("Projection Date")
    plt.ylabel("Cash Flow Amount")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    """Run all examples."""
    print("Fixed Income Model Usage Examples")
    print("=" * 50)
    
    example_1_basic_projection()
    example_2_portfolio_metrics()
    example_3_scenario_analysis()

if __name__ == "__main__":
    main()
